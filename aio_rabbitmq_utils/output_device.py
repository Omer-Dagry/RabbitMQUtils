from io import BytesIO
from typing import Optional

from aio_pika import DeliveryMode, RobustExchange, Message
from aio_pika.abc import HeadersType
from pamqp.commands import Basic

from .base_device import RabbitMQBaseOutputDevice
from .device_manager import RabbitMQDeviceManager


class RabbitMQOutputDevice(RabbitMQBaseOutputDevice):
    def __init__(
            self,
            device_manager: RabbitMQDeviceManager,
            device_name: str,
            exchange_name: str,
    ):
        self._device_manager = device_manager
        self._device_name = device_name
        self._exchange_name = exchange_name

        self._exchange: Optional[RobustExchange] = None

    @property
    async def exchange(self) -> Optional[RobustExchange]:
        if self._exchange is None or self._exchange.channel.is_closed:
            self._exchange = await (await self._device_manager.channel).get_exchange(
                self._exchange_name,
                ensure=self._exchange_name != "",
            )
        return self._exchange

    async def send(
            self,
            stream: BytesIO,
            headers: Optional[HeadersType] = None,
            delivery_mode: DeliveryMode = DeliveryMode.PERSISTENT
    ) -> bool:
        return await (await self.exchange).publish(
            Message(
                body=stream.read(),
                headers=headers,
                delivery_mode=delivery_mode,
            ),
            routing_key=self._device_name,
        ) == Basic.Ack

    async def connect(self) -> None:
        self._exchange = await self.exchange

    async def close(self) -> None:
        pass
