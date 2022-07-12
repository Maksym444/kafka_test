import asyncio
import json
import os

import django
import time
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

STARTUP_DELAY = 15
CONSUME_POLL_INTERVAL_SEC = 1
PRODUCE_POLL_INTERVAL_SEC = 10*60
READ_TIMEOUT_SEC = 1

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from producer import models


async def produce():
    producer = AIOKafkaProducer(bootstrap_servers='kafka:9092')
    await producer.start()

    try:
        while True:
            channels = await models.Channel.all()
            for channel in channels:
                res = await producer.send_and_wait("topic", json.dumps({
                    'url': channel.url,
                    'last_message_id': channel.last_message_id
                }).encode())
                print('Sent message with RESULT: ', res)


            print('[PRODUCER] Sleeping till the next attempt...')
            await asyncio.sleep(PRODUCE_POLL_INTERVAL_SEC)

    except Exception as ex:
        print('EXCEPTION:', ex)
    finally:
        await producer.stop()


async def consume():
    consumer = AIOKafkaConsumer(
        'topic_result',
        bootstrap_servers='kafka:9092',
    )
    await consumer.start()

    try:
        while True:
            data = await consumer.getmany(timeout_ms=READ_TIMEOUT_SEC*1000)
            for tp, messages in data.items():
                for msg in messages:
                    payload = json.loads(msg.value.decode())
                    channel = await models.Channel.update_by_filter(
                        filters={'url': payload['channel_url']},
                        data={'last_message_id': payload['id']}
                    )
                    print("consumed: ", msg.topic, msg.partition, msg.offset,
                          msg.key, msg.value, msg.timestamp)
                    print("Updated channel: ", channel)
            print('[CONSUMER] Sleeping till the next attempt...')
            await asyncio.sleep(CONSUME_POLL_INTERVAL_SEC)

    except Exception as ex:
        print("EXCEPTION: ", ex)

    finally:
        # Will leave consumer group; perform autocommit if enabled.
        await consumer.stop()


async def start_coros():
    consume_task = asyncio.create_task(consume())
    produce_task = asyncio.create_task(produce())
    await asyncio.wait([consume_task, produce_task])


def main():
    print(f'PRODUCER: wait until broker is up and running {STARTUP_DELAY}...')
    time.sleep(STARTUP_DELAY)
    print('PRODUCER: start writing messages!')

    asyncio.run(start_coros())

if __name__ == '__main__':
    main()

