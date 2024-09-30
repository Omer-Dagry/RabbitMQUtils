from abc import ABC, abstractmethod

from aio_pika.abc import AbstractIncomingMessage


class BaseTransaction(ABC):
    @abstractmethod
    async def commit(self) -> None:
        raise NotImplemented

    @abstractmethod
    async def rollback(self) -> None:
        raise NotImplemented

    @abstractmethod
    async def is_done(self) -> bool:
        raise NotImplemented


class RabbitMQIncomingMessageTransaction(BaseTransaction):
    def __init__(self, incoming_message: AbstractIncomingMessage) -> None:
        self._incoming_message = incoming_message
        self._is_done = False

    async def commit(self) -> None:
        await self._incoming_message.ack()
        self._is_done = True

    async def rollback(self) -> None:
        await self._incoming_message.nack()
        self._is_done = True

    async def is_done(self) -> bool:
        return self._is_done


class EmptyTransaction(BaseTransaction):
    def __init__(self) -> None:
        self._is_done = False

    async def commit(self) -> None:
        self._is_done = True

    async def rollback(self) -> None:
        self._is_done = True

    async def is_done(self) -> bool:
        return self._is_done
