from io import BytesIO
from typing import Dict, Optional, Tuple

from aio_pika.abc import HeadersType

from .base_device import RabbitMQBaseInputDevice
from .multi_connection_device_manager import RabbitMQMultiConnectionDeviceManager
from .transaction import BaseTransaction, EmptyTransaction, RabbitMQIncomingMessageTransaction


class RabbitMQInputBasicGetDevice(RabbitMQBaseInputDevice):
    def __init__(
        self,
        device_manager: RabbitMQMultiConnectionDeviceManager,
        device_name: str,
        use_transaction: bool,
        max_channels: int,
    ):
        self._device_manager = device_manager
        self._device_name = device_name
        self._use_transaction = use_transaction
        self._max_channels = max_channels
        self._channel_number_to_max_delivery_tag: Dict[int, Optional[int]] = {}

    async def _inner_commit_rollback_all_messages(self, *, commit: bool) -> None:
        if not self._channel_number_to_max_delivery_tag:
            raise Exception("No messages to commit/rollback")

        channel_pool = await self._device_manager.channel
        # noinspection PyProtectedMember
        channels = [await channel_pool._get() for _ in range(self._max_channels)]
        for channel in channels:
            max_delivery_tag_for_channel = self._channel_number_to_max_delivery_tag.pop(channel.number, None)
            if max_delivery_tag_for_channel is None:
                continue

            aiormq_channel = await channel.get_underlay_channel()
            func = aiormq_channel.basic_ack if commit else aiormq_channel.basic_nack
            return await func(delivery_tag=max_delivery_tag_for_channel, multiple=True)

        return None

    async def commit_all_messages(self) -> None:
        return await self._inner_commit_rollback_all_messages(commit=True)

    async def rollback_all_messages(self) -> None:
        return await self._inner_commit_rollback_all_messages(commit=False)

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

            self._channel_number_to_max_delivery_tag[channel.number] = max(
                incoming_message.delivery_tag,
                self._channel_number_to_max_delivery_tag.pop(channel.number, -1),  # -1 because delivery tag is positive
            )
            return BytesIO(incoming_message.body), incoming_message.headers, transaction

    async def connect(self) -> None:
        pass

    async def close(self) -> None:
        pass
