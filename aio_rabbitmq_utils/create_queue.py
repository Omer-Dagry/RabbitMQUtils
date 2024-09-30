from typing import Dict, Union, List

from aio_pika.abc import AbstractQueue

from .device_manager import RabbitMQDeviceManager


async def declare_queue(
        device_manager: RabbitMQDeviceManager,
        queue_name: str,
        arguments: Dict[str, Union[str, int, List[str]]] = None,
        durable: bool = True,
) -> AbstractQueue:
    return await (await device_manager.channel).declare_queue(
        name=queue_name,
        durable=durable,
        arguments=arguments,
    )
