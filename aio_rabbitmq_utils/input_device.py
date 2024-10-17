from io import BytesIO
from typing import Optional, Tuple

from aio_pika.abc import HeadersType

from .base_device import RabbitMQBaseInputDevice
from .multi_connection_device_manager import RabbitMQMultiConnectionDeviceManager
from .transaction import BaseTransaction, RabbitMQIncomingMessageTransaction, EmptyTransaction


class RabbitMQInputBasicGetDevice(RabbitMQBaseInputDevice):
    def __init__(
            self,
            device_manager: RabbitMQMultiConnectionDeviceManager,
            device_name: str,
            use_transaction: bool,
    ):
        self._device_manager = device_manager
        self._device_name = device_name
        self._use_transaction = use_transaction

    async def commit_all_messages(self) -> None:
        raise NotImplemented("Not implemented for multi-connection")

    async def rollback_all_messages(self) -> None:
        raise NotImplemented("Not implemented for multi-connection")

    @property
    def has_messages_available(self) -> bool:
        return False

    async def read(
            self,
    ) -> Optional[Tuple[BytesIO, HeadersType, BaseTransaction]]:
        async with (await self._device_manager.channel).acquire() as channel:
            queue = await channel.get_queue(self._device_name)

            incoming_message = await queue.get(no_ack=not self._use_transaction, fail=False)
            if incoming_message is None:
                return None

            transaction = RabbitMQIncomingMessageTransaction(incoming_message) if self._use_transaction \
                else EmptyTransaction()

            return BytesIO(incoming_message.body), incoming_message.headers, transaction

    async def connect(self) -> None:
        pass

    async def close(self) -> None:
        pass
