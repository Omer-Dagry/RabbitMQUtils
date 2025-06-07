from asyncio import Lock
from collections import deque
from io import BytesIO
from typing import Deque, Optional, TYPE_CHECKING, Tuple

from aio_pika import RobustQueue
from aio_pika.abc import AbstractIncomingMessage, ConsumerTag, HeadersType
from no_exception import NoException
from pamqp.common import Arguments

from .base_device import RabbitMQBaseInputDevice
from .transaction import BaseTransaction, EmptyTransaction, RabbitMQIncomingMessageTransaction

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
        self._max_delivery_tag: Optional[int] = None

    async def _inner_commit_rollback_all_messages(self, commit: bool) -> None:
        if not self._max_delivery_tag:
            raise Exception("No messages to commit/rollback")

        channel = await self._device_manager.channel
        aiormq_channel = await channel.get_underlay_channel()
        # delivery_tag=0 + multiple=True means ack/nack all un-acked messages in the channel
        func = aiormq_channel.basic_ack if commit else aiormq_channel.basic_nack
        return await func(delivery_tag=self._max_delivery_tag, multiple=True)

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
            channel = await self._device_manager.channel
            self._queue = await channel.get_queue(self._device_name)
        return self._queue

    async def _inner_consume(
        self,
        incoming_message: AbstractIncomingMessage,
    ) -> None:
        transaction = RabbitMQIncomingMessageTransaction(incoming_message) \
            if self._use_transaction else EmptyTransaction()
        async with self._lock:
            self._inner_queue.append(
                (
                    BytesIO(incoming_message.body),
                    incoming_message.headers,
                    transaction,
                ),
            )

    async def read(
        self,
    ) -> Optional[Tuple[BytesIO, HeadersType, BaseTransaction]]:
        async with self._lock:
            try:
                data, headers, transaction = self._inner_queue.popleft()
                if self._use_transaction:
                    self._max_delivery_tag = max(
                        transaction._incoming_message.delivery_tag,
                        self._max_delivery_tag,
                    )
                return data, headers, transaction
            except IndexError:
                return None

    async def connect(self) -> None:
        self._consumer_tag = await (await self.queue).consume(
            self._inner_consume,
            no_ack=not self._use_transaction,
            arguments=self._consumer_arguments,
        )

    async def close(self) -> None:
        async with self._lock:
            for _, _, transaction in self._inner_queue:
                with NoException():
                    await transaction.rollback()
            self._inner_queue.clear()
        await (await self.queue).cancel(self._consumer_tag)
