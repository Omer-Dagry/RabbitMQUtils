from io import BytesIO
from typing import Optional, Tuple, List

from aio_pika.abc import HeadersType, AbstractIncomingMessage
from pamqp.common import Arguments

from rabbitmq_utils.base_device import RabbitMQBaseInputDevice
from rabbitmq_utils.device_manager import RabbitMQDeviceManager
from rabbitmq_utils.transaction import BaseTransaction, RabbitMQIncomingMessageTransaction, EmptyTransaction


class RabbitMQInputConsumeDevice(RabbitMQBaseInputDevice):
    def __init__(
            self,
            device_manager: RabbitMQDeviceManager,
            device_name: str,
            use_transaction: bool,
            consumer_arguments: Arguments = None,
    ):
        self._device_manager = device_manager
        self._device_name = device_name
        self._use_transaction = use_transaction
        self._consumer_arguments = consumer_arguments

        self._inner_queue: List[Tuple[BytesIO, HeadersType, BaseTransaction]] = []

    async def _inner_consume(
            self,
            incoming_message: AbstractIncomingMessage,
    ) -> None:
        transaction = RabbitMQIncomingMessageTransaction(incoming_message) if self._use_transaction \
            else EmptyTransaction()
        self._inner_queue.append((BytesIO(incoming_message.body), incoming_message.headers, transaction))

    async def read(
            self,
    ) -> Optional[Tuple[BytesIO, HeadersType, BaseTransaction]]:
        if self._inner_queue:
            return self._inner_queue.pop(0)
        return None

    async def connect(self) -> None:
        queue = await (await self._device_manager.channel).get_queue(self._device_name)
        await queue.consume(
            self._inner_consume,
            arguments=self._consumer_arguments
        )

    async def close(self) -> None:
        for _, _, transaction in self._inner_queue:
            try:
                await transaction.rollback()
            except:
                pass
        self._inner_queue = []
