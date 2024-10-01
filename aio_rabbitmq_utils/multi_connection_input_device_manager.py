from typing import Dict, Any, List

from pamqp.constants import DEFAULT_PORT

from .base_device_manager import RabbitMQBaseInputDeviceManager
from .input_device import RabbitMQInputBasicGetDevice
from .multi_connection_device_manager import RabbitMQMultiConnectionDeviceManager


class RabbitMQMultiConnectionBasicGetInputDeviceManager(
    RabbitMQMultiConnectionDeviceManager,
    RabbitMQBaseInputDeviceManager,
):
    def __init__(
            self,
            hosts: List[str],
            user: str,
            password: str,
            vhost: str,
            max_connections: int,
            max_channels: int,
            channel_qos_kwargs: Dict[str, Any] = None,
            use_transaction: bool = True,
            use_ssl: bool = False,
            port: int = DEFAULT_PORT,
    ):
        super().__init__(
            hosts=hosts,
            user=user,
            password=password,
            vhost=vhost,
            publisher_confirms=False,
            max_connections=max_connections,
            max_channels=max_channels,
            channel_qos_kwargs=channel_qos_kwargs,
            use_transaction=use_transaction,
            use_ssl=use_ssl,
            port=port,
        )

    async def get_device(
            self,
            device_name: str,
    ) -> RabbitMQInputBasicGetDevice:
        return RabbitMQInputBasicGetDevice(
            self,
            device_name,
            self._use_transaction,
        )
