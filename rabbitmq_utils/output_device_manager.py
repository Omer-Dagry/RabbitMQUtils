from typing import List, Dict, Any

from pamqp.constants import DEFAULT_PORT

from rabbitmq_utils import RabbitMQOutputDevice, RabbitMQDeviceManager
from rabbitmq_utils.base_device_manager import RabbitMQBaseOutputDeviceManager


class RabbitMQOutputDeviceManager(
    RabbitMQDeviceManager,
    RabbitMQBaseOutputDeviceManager,
):
    def __init__(
            self,
            hosts: List[str],
            user: str,
            password: str,
            vhost: str,
            publisher_confirms: bool,
            exchange_name: str,
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
        self._exchange_name = exchange_name

    async def get_device(
            self,
            device_name: str,
    ) -> RabbitMQOutputDevice:
        return RabbitMQOutputDevice(
            self,
            device_name,
            self._exchange_name
        )
