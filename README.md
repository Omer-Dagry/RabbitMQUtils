# RabbitMQUtils

### Example for reader
#### Consumer

```python
from aio_rabbitmq_utils import RabbitMQConsumeInputDeviceManager, RabbitMQInputConsumeDevice


async def example():
    input_device_manager = RabbitMQConsumeInputDeviceManager(
        hosts=["the", "rabbit", "hosts", ", will", "connect", "to", "only", "one"],
        user="user",
        password="password",
        vhost="/",
    )
    await input_device_manager.connect()
    input_device: RabbitMQInputConsumeDevice = await input_device_manager.get_device("some_queue_name")
    await input_device.connect()
    data, headers, transaction = await input_device.read()
    
    # do something
    
    # To ack the message (remove from queue)
    await transaction.commit()
    # To nack the message (re-queue the message)
    await transaction.rollback()
```
#### Basic Get

```python
from aio_rabbitmq_utils import RabbitMQMultiConnectionBasicGetInputDeviceManager, RabbitMQInputBasicGetDevice


async def example():
    input_device_manager = RabbitMQMultiConnectionBasicGetInputDeviceManager(
        hosts=["the", "rabbit", "hosts", ", will", "connect", "to", "only", "one"],
        user="user",
        password="password",
        vhost="/",
        max_connections=10,
        max_channels=50,
    )
    await input_device_manager.connect()
    input_device: RabbitMQInputBasicGetDevice = await input_device_manager.get_device("some_queue_name")
    await input_device.connect()
    data, headers, transaction = await input_device.read()
    
    # do something
    
    # To ack the message (remove from queue)
    await transaction.commit()
    # To nack the message (re-queue the message)
    await transaction.rollback()
```

### Example for writer

```python
from io import BytesIO
from aio_rabbitmq_utils import RabbitMQOutputDeviceManager, RabbitMQOutputDevice


async def example():
    output_device_manager = RabbitMQOutputDeviceManager(
        hosts=["the", "rabbit", "hosts", ", will", "connect", "to", "only", "one"],
        user="user",
        password="password",
        vhost="/",
        publisher_confirms=True,
        exchange_name="",
    )
    await output_device_manager.connect()
    output_device: RabbitMQOutputDevice = await output_device_manager.get_device("some_routing_key")
    await output_device.connect()
    success = await output_device.send(
        BytesIO(b"Hi"),
        {"some": "headers"},
    )
    if success:
        print("Message sent")
    else:
        raise Exception("Failed to send the message")
```