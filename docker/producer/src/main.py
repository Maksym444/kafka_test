import asyncio
import json
import os

import django
import time
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from kafka import TopicPartition
from logger import logger


STARTUP_DELAY = 15
CONSUME_POLL_INTERVAL_SEC = 5
PRODUCE_POLL_INTERVAL_SEC = 20*60*60
READ_TIMEOUT_SEC = 1
PARTITIONS_COUNT = int(os.getenv('KAFKA_PARTITIONS_NUM', 8))
SIZE_KB = 1024
SIZE_MB = SIZE_KB*SIZE_KB
KAFKA_HOST = os.getenv('KAFKA_HOST')
KAFKA_PORT = os.getenv('KAFKA_PORT')


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from producer import models


async def producer():
    producer = AIOKafkaProducer(bootstrap_servers=f'{KAFKA_HOST}:{KAFKA_PORT}')
    await producer.start()

    try:
        while True:
            channels = await models.Channel.all()
            for idx, channel in enumerate(channels):
                payload = json.dumps({
                    'url': channel.url,
                    'last_message_id': channel.last_message_id
                }).encode()
                res = await producer.send_and_wait(
                    topic="topic",
                    # key=int(channel.channel_id),
                    value=payload,
                    partition=idx%PARTITIONS_COUNT
                )
                logger.info(f'Sent message with RESULT: {res}')


            logger.info('[PRODUCER] Sleeping till the next attempt...')
            await asyncio.sleep(PRODUCE_POLL_INTERVAL_SEC)

    except Exception as ex:
        logger.error(f'EXCEPTION: {ex}')
    finally:
        await producer.stop()


async def consumer(partition_id):
    consumer = AIOKafkaConsumer(
        # 'topic_result',
        group_id='consumers-group',
        bootstrap_servers='kafka:9092',
        max_partition_fetch_bytes=SIZE_MB * 1,
        fetch_max_bytes=SIZE_MB * 50
    )
    await consumer.start()
    consumer.assign([TopicPartition('topic_result', partition_id)])

    while True:
        try:
            data = await consumer.getmany(timeout_ms=READ_TIMEOUT_SEC*1000)
            for tp, messages in data.items():
                for msg in messages:
                    payload = json.loads(msg.value.decode())
                    channel = await models.Channel.update_by_filter(
                        filters={'url': payload['channel_url']},
                        data={
                            'last_message_id': payload['id'],
                            'last_message_ts': payload['date'],
                        }
                    )
                    logger.info("consumed: %s, %s, %s, %s, %s, %s", msg.topic, msg.partition, msg.offset,
                          msg.key, msg.value, msg.timestamp)
                    logger.info("Updated channel: %s", channel)
            logger.info(f'[CONSUMER] PARTITION_ID {partition_id}: Sleeping till the next attempt...')
            await asyncio.sleep(CONSUME_POLL_INTERVAL_SEC)

        except Exception as ex:
            logger.error("EXCEPTION: %s", ex)

    # finally:
    #     await consumer.stop()


async def start_coros():
    consumers = [consumer(i) for i in range(PARTITIONS_COUNT)]
    await asyncio.gather(*consumers, producer())


def main():
    logger.info(f'PRODUCER: wait until broker is up and running {STARTUP_DELAY}...')
    time.sleep(STARTUP_DELAY)
    logger.info('PRODUCER: start writing messages!')
    asyncio.run(start_coros())


if __name__ == '__main__':
    main()

