from asyncio import Lock
from collections import deque
from io import BytesIO
from typing import Optional, Tuple, Deque, TYPE_CHECKING

from aio_pika import RobustQueue
from aio_pika.abc import HeadersType, AbstractIncomingMessage, ConsumerTag
from no_exception import NoException
from pamqp.common import Arguments

from .base_device import RabbitMQBaseInputDevice
from .transaction import BaseTransaction, RabbitMQIncomingMessageTransaction, EmptyTransaction

if TYPE_CHECKING:
    from aio_rabbitmq_utils import RabbitMQConsumeInputDeviceManager


class RabbitMQInputConsumeDevice(RabbitMQBaseInputDevice):
    def __init__(
            self,
            device_manager: "RabbitMQConsumeInputDeviceManager",
            device_name: str,
            use_transaction: bool,
            consumer_arguments: Arguments = None,
    ):
        self._device_manager = device_manager
        self._device_name = device_name
        self._use_transaction = use_transaction
        self._consumer_arguments = consumer_arguments

        self._lock = Lock()
        self._queue: Optional[RobustQueue] = None
        self._consumer_tag: Optional[ConsumerTag] = None
        self._inner_queue: Deque[Tuple[BytesIO, HeadersType, BaseTransaction]] = deque([])

    async def _inner_commit_rollback_all_messages(self, commit: bool) -> None:
        channel = self._device_manager.run_in_executor(self._device_manager.channel)
        aiormq_channel = self._device_manager.run_in_executor(channel.get_underlay_channel())
        # delivery_tag=0 + multiple=True means ack/nack all un-acked messages in the channel
        func = aiormq_channel.basic_ack if commit else aiormq_channel.basic_nack
        return self._device_manager.run_in_executor(func(delivery_tag=0, multiple=True))

    async def commit_all_messages(self) -> None:
        return await self._inner_commit_rollback_all_messages(commit=True)

    async def rollback_all_messages(self) -> None:
        return await self._inner_commit_rollback_all_messages(commit=False)

    @property
    def has_messages_available(self) -> bool:
        return len(self._inner_queue) > 0

    @property
    async def queue(self) -> RobustQueue:
        if self._queue is None or self._queue.channel.is_closed:
            channel = self._device_manager.run_in_executor(self._device_manager.channel)
            self._queue = self._device_manager.run_in_executor(channel.get_queue(self._device_name))
        return self._queue

    async def _inner_consume(
            self,
            incoming_message: AbstractIncomingMessage,
    ) -> None:
        transaction = RabbitMQIncomingMessageTransaction(incoming_message, self._device_manager.run_in_executor) \
            if self._use_transaction else EmptyTransaction()
        async with self._lock:
            self._inner_queue.append((BytesIO(incoming_message.body), incoming_message.headers, transaction))

    async def read(
            self,
    ) -> Optional[Tuple[BytesIO, HeadersType, BaseTransaction]]:
        async with self._lock:
            try:
                return self._inner_queue.popleft()
            except IndexError:
                return None

    async def connect(self) -> None:
        self._consumer_tag = self._device_manager.run_in_executor(
            (await self.queue).consume(
                self._inner_consume,
                no_ack=not self._use_transaction,
                arguments=self._consumer_arguments
            )
        )

    async def close(self) -> None:
        async with self._lock:
            for _, _, transaction in self._inner_queue:
                with NoException():
                    self._device_manager.run_in_executor(transaction.rollback())
            self._inner_queue.clear()
        self._device_manager.run_in_executor((await self.queue).cancel(self._consumer_tag))
