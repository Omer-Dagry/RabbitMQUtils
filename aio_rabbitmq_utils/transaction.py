from abc import ABC, abstractmethod
from typing import Callable, Coroutine, Any, TypeVar

from aio_pika.abc import AbstractIncomingMessage

T = TypeVar('T')


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
    def __init__(
            self,
            incoming_message: AbstractIncomingMessage,
            run_in_executor: Callable[[Coroutine[Any, Any, T]], T] = None,
    ) -> None:
        self._incoming_message = incoming_message
        self._run_in_executor = run_in_executor

        self._is_done = False

    async def commit(self) -> None:
        if self._run_in_executor:
            self._run_in_executor(self._incoming_message.ack())
        else:
            await self._incoming_message.ack()
        self._is_done = True

    async def rollback(self) -> None:
        if self._run_in_executor:
            self._run_in_executor(self._incoming_message.nack())
        else:
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
