import itertools

import os

import asyncio
import json

import time
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from kafka import TopicPartition

import parser
from logger import logger


STARTUP_DELAY = 10
CONSUME_POLL_INTERVAL_SEC = 5
READ_TIMEOUT_SEC = 1
PARTITIONS_COUNT = int(os.getenv('KAFKA_PARTITIONS_NUM', 8))
SIZE_KB = 1024
SIZE_MB = SIZE_KB*SIZE_KB
KAFKA_HOST = os.getenv('KAFKA_HOST')
KAFKA_PORT = os.getenv('KAFKA_PORT')


async def consumer(partition_id):
    consumer = AIOKafkaConsumer(
        # 'topic',
        bootstrap_servers=f'{KAFKA_HOST}:{KAFKA_PORT}',
        group_id='consumers-group',
        max_partition_fetch_bytes=SIZE_MB*1,
        fetch_max_bytes=SIZE_MB*50
    )
    # consumer.assign([TopicPartition('topic', partition_id)])
    consumer.assign([TopicPartition('topic', 0)])
    # producer = AIOKafkaProducer(bootstrap_servers=f'{KAFKA_HOST}:{KAFKA_PORT}')

    await consumer.start()
    # await producer.start()

    while True:
        try:
            # async for task in consumer:
            data = await consumer.getmany(timeout_ms=READ_TIMEOUT_SEC*1000)
            for tp, messages in data.items():
                for message in messages:
                    logger.info(f'PARTITION_ID {partition_id}: received message: %s', message)
                    # logger.info(f'PARTITION_ID {partition_id}: received message: %s', message.value.decode())
                    # task = json.loads(message.value.decode())

                    # async for msg in parser.get_messages(parser.client, task['url'], task['last_message_id']):
                    #     await producer.send_and_wait("topic_result", json.dumps(msg).encode(), partition=partition_id)
                    #     logger.info(f'PARTITION_ID {partition_id}: Replied with msg={msg}')

            logger.info(f'PARTITION_ID {partition_id}: Sleeping till the next attempt...')
            # logger.info(' PARTITION_ID: Sleeping till the next attempt...')
            await asyncio.sleep(CONSUME_POLL_INTERVAL_SEC)


        except Exception as ex:
            logger.error('EXCEPTION: %s', ex)

    # await consumer.stop()
    # await producer.stop()


async def start_coros():
    # consumers = [consumer(i) for i in range(PARTITIONS_COUNT)]
    consumers = [consumer(i) for i in itertools.repeat(0, 8)]
    await asyncio.gather(*consumers)


def main():
    logger.info(f'CONSUMER: wait until broker is up and running {STARTUP_DELAY}...')
    time.sleep(STARTUP_DELAY)
    logger.info('CONSUMER: start reading messages!')

    with parser.client:
        # loop = asyncio.get_event_loop()
        # loop.run_until_complete(start_coros())
        asyncio.run(start_coros())


if __name__ == '__main__':
    main()