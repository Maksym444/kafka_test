import asyncio
import json
import os
import time

import django
from aiokafka import AIOKafkaConsumer
from kafka import TopicPartition

from logger import logger

STARTUP_DELAY = 15
CONSUME_POLL_INTERVAL_SEC = 5
READ_TIMEOUT_SEC = 1
PARTITIONS_COUNT = int(os.getenv('KAFKA_PARTITIONS_NUM', 8))
SIZE_KB = 1024
SIZE_MB = SIZE_KB*SIZE_KB
KAFKA_HOST = os.getenv('KAFKA_HOST')
KAFKA_PORT = os.getenv('KAFKA_PORT')
PROCESSOR_SCALE_FACTOR = int(os.getenv('PROCESSOR_SCALE_FACTOR'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from producer import models


async def consume(partition_id):
    consumer = AIOKafkaConsumer(
        'topic_result',
        group_id='consumers-group',
        bootstrap_servers=f'{KAFKA_HOST}:{KAFKA_PORT}',
        max_partition_fetch_bytes=SIZE_MB * 1,
        fetch_max_bytes=SIZE_MB * 50
    )
    await consumer.start()
    # consumer.assign([TopicPartition('topic_result', partition_id)])

    while True:
        try:
            data = await consumer.getmany(timeout_ms=READ_TIMEOUT_SEC*1000)
            if data:
                for tp, messages in data.items():
                    # logger.info("Received mesasges: %s", tp)
                    for msg in messages:
                        payload = json.loads(msg.value.decode())
                        channel = await models.Channel.upsert_by_filter(
                            filters={'url': payload['channel_url']},
                            data={
                                'url': payload['channel_url'],
                                'last_message_id': payload['id'],
                                'last_message_ts': payload['date'],
                            }
                        )
                        logger.info("consumed: %s, %s, %s, %s, %s, %s", msg.topic, msg.partition, msg.offset,
                              msg.key, msg.value, msg.timestamp)
                        logger.info("Updated channel: %s", channel)
            else:
                logger.info(f'[CONSUMER] PARTITION_ID {partition_id}: Sleeping till the next attempt...')
                await asyncio.sleep(CONSUME_POLL_INTERVAL_SEC)

        except Exception as ex:
            logger.error("EXCEPTION: %s", ex)


async def start_coros():
    consumers = [consume(i) for i in range(PARTITIONS_COUNT//PROCESSOR_SCALE_FACTOR)]
    # await asyncio.gather(*consumers, producer())
    await asyncio.gather(*consumers)


def main():
    logger.info(f'PROCESSOR: wait until broker is up and running {STARTUP_DELAY}...')
    time.sleep(STARTUP_DELAY)
    logger.info('PROCESSOR: start processing messages!')
    asyncio.run(start_coros())


if __name__ == '__main__':
    main()
