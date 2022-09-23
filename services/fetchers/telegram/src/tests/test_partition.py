import asyncio
import logging
import os
import time
from aiokafka import AIOKafkaConsumer

# ----------------------------------------------------------------------------------------------------------------------
# log_file = "../log/consumer1.log"
# log_level = logging.INFO
# logging.basicConfig(
#     level=log_level, filename=log_file, filemode="a+", format="%(asctime)-15s %(levelname)-8s %(message)s"
# )
# logger = logging.getLogger("date_parser")
# logger.addHandler(logging.StreamHandler())
from kafka import TopicPartition

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
        'topic',
        bootstrap_servers=f'{KAFKA_HOST}:{KAFKA_PORT}',
        group_id='consumers-group',
        max_partition_fetch_bytes=SIZE_MB*1,
        fetch_max_bytes=SIZE_MB*50
    )

    # consumer.assign([TopicPartition('topic', partition_id)])
    # consumer.assign([TopicPartition('topic', 0)])
    await consumer.start()

    while True:
        try:
            # async for task in consumer:
            data = await consumer.getmany(timeout_ms=READ_TIMEOUT_SEC*1000, max_records=1)
            for tp, messages in data.items():
                for message in messages:
                    # logger.info(f'PARTITION_ID {partition_id}: received message: %s', message)
                    print(f'PARTITION_ID {partition_id}: received message: %s', message)


            # logger.info(f'PARTITION_ID {partition_id}: Sleeping till the next attempt...')
            print(f'PARTITION_ID {partition_id}: Sleeping till the next attempt...')
            # logger.info(' PARTITION_ID: Sleeping till the next attempt...')
            await asyncio.sleep(CONSUME_POLL_INTERVAL_SEC)


        except Exception as ex:
            # logger.error('EXCEPTION: %s', ex)
            print('EXCEPTION: %s', ex)

    # await consumer.stop()
    # await producer.stop()


async def start_coros():
    consumers = [consumer(i) for i in range(PARTITIONS_COUNT)]
    # consumers = [consumer(i) for i in range(1)]
    # consumers = [consumer(i) for i in itertools.repeat(0, 8)]
    await asyncio.gather(*consumers)


def main():
    # logger.info(f'CONSUMER: wait until broker is up and running {STARTUP_DELAY}...')
    print(f'CONSUMER: wait until broker is up and running {STARTUP_DELAY}...')
    time.sleep(STARTUP_DELAY)
    # logger.info('CONSUMER: start reading messages!')
    print('CONSUMER: start reading messages!')

    # with parser.client:
        # loop = asyncio.get_event_loop()
        # loop.run_until_complete(start_coros())
    asyncio.run(start_coros())


if __name__ == '__main__':
    main()