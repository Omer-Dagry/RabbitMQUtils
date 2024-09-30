from abc import ABC, abstractmethod

from .base_device import RabbitMQBaseDevice, RabbitMQBaseInputDevice, RabbitMQBaseOutputDevice


class RabbitMQBaseDeviceManager(ABC):
    @abstractmethod
    async def connect(self) -> None:
        raise NotImplemented

    @abstractmethod
    async def close(self) -> None:
        raise NotImplemented

    @abstractmethod
    async def get_device(
            self,
            device_name: str,
    ) -> RabbitMQBaseDevice:
        raise NotImplemented


class RabbitMQBaseInputDeviceManager(RabbitMQBaseDeviceManager):
    @abstractmethod
    async def get_device(
            self,
            device_name: str,
    ) -> RabbitMQBaseInputDevice:
        raise NotImplemented


class RabbitMQBaseOutputDeviceManager(RabbitMQBaseDeviceManager):
    @abstractmethod
    async def get_device(
            self,
            device_name: str,
    ) -> RabbitMQBaseOutputDevice:
        raise NotImplemented
