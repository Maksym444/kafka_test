import asyncio
import django
import logging
import os
import time
from aiokafka import AIOKafkaProducer

# ----------------------------------------------------------------------------------------------------------------------
log_file = "../log/consumer1.log"
log_level = logging.INFO
logging.basicConfig(
    level=log_level, filename=log_file, filemode="a+", format="%(asctime)-15s %(levelname)-8s %(message)s"
)
logger = logging.getLogger("date_parser")
logger.addHandler(logging.StreamHandler())


STARTUP_DELAY = 15
CONSUME_POLL_INTERVAL_SEC = 5
PRODUCE_POLL_INTERVAL_SEC = 20*60*60
READ_TIMEOUT_SEC = 1
# PARTITIONS_COUNT = int(os.getenv('KAFKA_PARTITIONS_NUM', 8))
PARTITIONS_COUNT = 2
SIZE_KB = 1024
SIZE_MB = SIZE_KB*SIZE_KB
KAFKA_HOST = os.getenv('KAFKA_HOST')
KAFKA_PORT = os.getenv('KAFKA_PORT')


async def producer():
    producer = AIOKafkaProducer(bootstrap_servers=f'{KAFKA_HOST}:{KAFKA_PORT}')
    await producer.start()

    try:
        while True:
            # channels = await models.Channel.all()
            for idx in range(100):
                # payload = json.dumps({
                #     'url': channel.url,
                #     'last_message_id': channel.last_message_id
                # }).encode()
                res = await producer.send_and_wait(
                    topic="topic",
                    # key=int(channel.channel_id),
                    value=f'{idx}'.encode(),
                    partition=idx%PARTITIONS_COUNT
                    # partition=0
                )
                logger.info(f'Sent message with RESULT: {res}')


            logger.info('[PRODUCER] Sleeping till the next attempt...')
            await asyncio.sleep(PRODUCE_POLL_INTERVAL_SEC)

    except Exception as ex:
        logger.error(f'EXCEPTION: {ex}')
    finally:
        await producer.stop()


async def start_coros():
    # consumers = [consumer(i) for i in range(PARTITIONS_COUNT)]
    # await asyncio.gather(*consumers, producer())
    await asyncio.gather(producer())


def main():
    logger.info(f'PRODUCER: wait until broker is up and running {STARTUP_DELAY}...')
    time.sleep(STARTUP_DELAY)
    logger.info('PRODUCER: start writing messages!')
    asyncio.run(start_coros())


if __name__ == '__main__':
    main()

