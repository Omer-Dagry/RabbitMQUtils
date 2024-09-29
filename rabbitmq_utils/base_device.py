from abc import ABC, abstractmethod
from io import BytesIO
from typing import Optional, Tuple

from aio_pika.abc import HeadersType, DeliveryMode

from rabbitmq_utils.transaction import BaseTransaction


class RabbitMQBaseDevice(ABC):
    @abstractmethod
    async def connect(self) -> None:
        raise NotImplemented

    @abstractmethod
    async def close(self) -> None:
        raise NotImplemented


class RabbitMQBaseInputDevice(RabbitMQBaseDevice, ABC):
    @abstractmethod
    async def read(
            self,
    ) -> Optional[Tuple[BytesIO, HeadersType, BaseTransaction]]:
        raise NotImplemented


class RabbitMQBaseOutputDevice(RabbitMQBaseDevice, ABC):
    @abstractmethod
    async def send(
            self,
            stream: BytesIO,
            headers: Optional[HeadersType] = None,
            delivery_mode: DeliveryMode = DeliveryMode.PERSISTENT,
    ) -> bool:
        raise NotImplemented
