from abc import ABC, abstractmethod

from aio_pika.abc import AbstractIncomingMessage


class BaseTransaction(ABC):
    @abstractmethod
    async def commit(self):
        raise NotImplemented

    @abstractmethod
    async def rollback(self):
        raise NotImplemented


class RabbitMQIncomingMessageTransaction(BaseTransaction):
    def __init__(self, incoming_message: AbstractIncomingMessage):
        self._incoming_message = incoming_message

    async def commit(self):
        await self._incoming_message.ack()

    async def rollback(self):
        await self._incoming_message.nack()


class EmptyTransaction(BaseTransaction):
    async def commit(self):
        pass

    async def rollback(self):
        pass
