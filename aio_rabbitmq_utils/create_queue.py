from typing import Dict, List

from aio_pika.abc import AbstractQueue

from .device_manager import RabbitMQDeviceManager


async def declare_queue(
    device_manager: RabbitMQDeviceManager,
    queue_name: str,
    passive: bool = False,
    arguments: Dict[str, str | int | List[str]] = None,
    durable: bool = True,
) -> AbstractQueue:
    return await (await device_manager.channel).declare_queue(
        name=queue_name,
        durable=durable,
        passive=passive,
        arguments=arguments,
    )
