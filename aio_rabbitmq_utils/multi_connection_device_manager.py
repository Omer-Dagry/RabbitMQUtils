import random
from abc import ABC
from typing import Optional, List, Any, Dict

from aio_pika import connect_robust
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel
from aio_pika.connection import make_url
from aio_pika.pool import Pool
from no_exception import NoException
from pamqp.constants import DEFAULT_PORT

from .device_manager import RabbitMQDeviceManager


class RabbitMQMultiConnectionDeviceManager(RabbitMQDeviceManager, ABC):
    def __init__(
            self,
            hosts: List[str],
            user: str,
            password: str,
            vhost: str,
            publisher_confirms: bool,
            max_connections: int,
            max_channels: int,
            channel_qos_kwargs: Dict[str, Any] = None,
            use_transaction: bool = False,
            use_ssl: bool = False,
            port: int = DEFAULT_PORT,
    ):
        super().__init__(
            hosts=hosts,
            user=user,
            password=password,
            vhost=vhost,
            publisher_confirms=publisher_confirms,
            channel_qos_kwargs=channel_qos_kwargs,
            use_transaction=use_transaction,
            use_ssl=use_ssl,
            port=port,
        )
        self._max_connections = max_connections
        self._max_channels = max_channels

        self._connection: Optional[Pool[AbstractRobustConnection]] = None
        self._channel: Optional[Pool[AbstractRobustChannel]] = None

    @property
    async def connection(self) -> Pool[AbstractRobustConnection]:
        return await super().connection

    @property
    async def channel(self) -> Pool[AbstractRobustChannel]:
        return await super().channel

    async def _create_connection(self) -> None:
        self._connection = Pool(
            connect_robust,
            make_url(
                host=random.choice(self._hosts),
                port=self._port,
                login=self._user,
                password=self._password,
                virtualhost=self._vhost,
                ssl=self._use_ssl,
            ),
            max_size=self._max_connections
        )

    async def _create_channel(self) -> None:
        async def inner_create_channel() -> AbstractRobustChannel:
            async with (await self.connection).acquire() as connection:
                channel = await connection.channel(
                    publisher_confirms=self._publisher_confirms,
                )
                await channel.set_qos(
                    **self._channel_qos_kwargs,
                )
                return channel

        self._channel = Pool(
            inner_create_channel,
            max_size=self._max_channels
        )

    async def _close_connection(self) -> None:
        with NoException():
            await self._connection.close()

    async def _close_channel(self) -> None:
        with NoException():
            await self._channel.close()
