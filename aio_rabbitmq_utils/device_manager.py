import random
from abc import ABC
from typing import Optional, List, Any, Dict

from aio_pika import connect_robust
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel
from aio_pika.connection import make_url
from no_exception import NoException
from pamqp.constants import DEFAULT_PORT

from .base_device_manager import RabbitMQBaseDeviceManager


class RabbitMQDeviceManager(RabbitMQBaseDeviceManager, ABC):
    def __init__(
            self,
            hosts: List[str],
            user: str,
            password: str,
            vhost: str,
            publisher_confirms: bool,
            channel_qos_kwargs: Dict[str, Any] = None,
            use_transaction: bool = False,
            use_ssl: bool = False,
            port: int = DEFAULT_PORT,
    ):
        self._hosts = hosts
        self._user = user
        self._password = password
        self._vhost = vhost
        self._publisher_confirms = publisher_confirms
        self._channel_qos_kwargs = channel_qos_kwargs or {}
        self._use_transaction = use_transaction
        self._use_ssl = use_ssl
        self._port = port

        self._connection: Optional[AbstractRobustConnection] = None
        self._channel: Optional[AbstractRobustChannel] = None

    async def connect(self) -> None:
        if self._connection is None or self._connection.is_closed or \
                self._channel is None or self._channel.is_closed:
            await self._reconnect()

    async def close(self) -> None:
        await self._close_channel()
        await self._close_connection()

    @property
    async def connection(self) -> AbstractRobustConnection:
        if self._connection is None or self._connection.is_closed:
            await self._reconnect()
        return self._connection

    @property
    async def channel(self) -> AbstractRobustChannel:
        if self._channel is None or self._channel.is_closed:
            await self._reconnect()
        return self._channel

    async def _reconnect(self) -> None:
        if self._connection is None or self._connection.is_closed:
            await self._create_connection()
        if self._channel is None or self._channel.is_closed:
            await self._create_channel()

    async def _create_connection(self) -> None:
        self._connection = await connect_robust(
            make_url(
                host=random.choice(self._hosts),
                port=self._port,
                login=self._user,
                password=self._password,
                virtualhost=self._vhost,
                ssl=self._use_ssl,
            ),
        )

    async def _create_channel(self) -> None:
        self._channel = await self._connection.channel(
            self._publisher_confirms,
        )
        await self._channel.set_qos(
            **self._channel_qos_kwargs,
        )

    async def _close_connection(self) -> None:
        with NoException():
            await self._connection.close()

    async def _close_channel(self) -> None:
        with NoException():
            await self._channel.close()
