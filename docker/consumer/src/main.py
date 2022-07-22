import datetime
import random
import atexit
import asyncio
import json
import os
import time
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from pymongo import ReturnDocument
from telethon.errors import FloodWaitError

import parser
from logger import logger
from models import TgAccount, TgChannel

from telethon import TelegramClient

STARTUP_DELAY = 10
CONSUME_POLL_INTERVAL_SEC = 5
READ_TIMEOUT_SEC = 1
PARTITIONS_COUNT = int(os.getenv('KAFKA_PARTITIONS_NUM', 8))
SIZE_KB = 1024
SIZE_MB = SIZE_KB*SIZE_KB
KAFKA_HOST = os.getenv('KAFKA_HOST')
KAFKA_PORT = os.getenv('KAFKA_PORT')
tg_account = None
TG_ERROR_MISSING_CHANNEL = 'Cannot find any entity corresponding to'

#
# async def consumer(partition_id):
#     consumer = AIOKafkaConsumer(
#         'topic',
#         bootstrap_servers=f'{KAFKA_HOST}:{KAFKA_PORT}',
#         group_id='consumers-group',
#         max_partition_fetch_bytes=SIZE_MB*1,
#         fetch_max_bytes=SIZE_MB*50
#     )
#     # consumer.assign([TopicPartition('topic', partition_id)])
#     producer = AIOKafkaProducer(bootstrap_servers=f'{KAFKA_HOST}:{KAFKA_PORT}')
#
#     await consumer.start()
#     await producer.start()
#
#     while True:
#         try:
#             # async for task in consumer:
#             data = await consumer.getmany(timeout_ms=READ_TIMEOUT_SEC*1000)
#             for tp, messages in data.items():
#                 for message in messages:
#                     logger.info(f'PARTITION_ID {partition_id}: received message: %s', message)
#                     task = json.loads(message.value.decode())
#
#                     async for msg in parser.get_messages(parser.client, task['url'], task['last_message_id']):
#                         await producer.send_and_wait("topic_result", json.dumps(msg).encode(), partition=partition_id)
#                         logger.info(f'PARTITION_ID {partition_id}: Replied with msg={msg}')
#
#             logger.info(f'PARTITION_ID {partition_id}: Sleeping till the next attempt...')
#             # logger.info(' PARTITION_ID: Sleeping till the next attempt...')
#             await asyncio.sleep(CONSUME_POLL_INTERVAL_SEC)
#
#         except Exception as ex:
#             logger.error('EXCEPTION: %s', ex)
#
#     # await consumer.stop()
#     # await producer.stop()


async def producer(partition_id, client):
    kafka_producer = AIOKafkaProducer(
        bootstrap_servers=f'{KAFKA_HOST}:{KAFKA_PORT}'
    )

    await kafka_producer.start()

    while True:
        channel_dict = TgChannel._get_collection().find_one_and_update(
            filter={'locked': False, 'enabled': True},
            update={'$set': {'locked': True}},
            return_document=ReturnDocument.AFTER
        )

        if channel_dict is None:
            raise RuntimeError('Couldn\'t find available TG channel!')

        channel=TgChannel.objects(url=channel_dict['url']).first()

        logger.info(f'PARTITION_ID {partition_id}: picked up channel: %s', channel)

        try:
            async for msg in parser.get_messages(client, channel.url, channel.channel_id, channel.last_message_id):
                # await kafka_producer.send_and_wait("topic_result", json.dumps(msg).encode(), partition=partition_id)
                await kafka_producer.send_and_wait("topic_result", json.dumps(msg).encode())
                logger.info(f'PARTITION_ID {partition_id}: Replied with msg={msg}')
                channel.last_message_id = msg['id']
                # channel.last_message_ts = msg['date']
                # channel.last_parsed = str(datetime.datetime.now())
                channel.save()

            channel.locked = False
            channel.save()

        except FloodWaitError as ex:
            # time.sleep(ex.seconds)
            logger.error('EXCEPTION: %s', ex)

        except Exception as ex:
            if TG_ERROR_MISSING_CHANNEL in str(ex):
                if channel:
                    channel.enabled = False
                    channel.save()

            logger.error('EXCEPTION: %s', ex)

        finally:
            logger.info(f'PARTITION_ID {partition_id}: Sleeping till the next attempt...')
            await asyncio.sleep(CONSUME_POLL_INTERVAL_SEC)


async def start_coros(client):
    # consumers = [consumer(i) for i in range(PARTITIONS_COUNT//2)]
    producers = [producer(i, client) for i in range(PARTITIONS_COUNT//2)]
    await asyncio.gather(*producers, loop=client.loop)


def exit_handler():
    if tg_account:
        account = TgAccount._get_collection().find_one_and_update(
            filter={'db_name': tg_account['db_name']},
            update={'$set': {'locked': False}},
            return_document=ReturnDocument.AFTER
        )
        logger.info('CONSUMER: restored account availability: %s', account)


def main():
    global tg_account
    atexit.register(exit_handler)
    logger.info(f'CONSUMER: wait until broker is up and running {STARTUP_DELAY}...')
    time.sleep(random.randint(STARTUP_DELAY, STARTUP_DELAY*2))
    logger.info('CONSUMER: start reading messages!')

    tg_account = TgAccount._get_collection().find_one_and_update(
        filter={'locked': False},
        update={'$set': {'locked': True}},
        return_document = ReturnDocument.AFTER
    )

    if tg_account is None:
        raise RuntimeError('Coudln\'t find available TG account!')

    client = TelegramClient(
        session=tg_account['db_name'],
        api_id=tg_account['app_id'],
        api_hash=tg_account['app_secret']
    )

    with client:
        # parser.client.loop.run_until_complete(consumer(0))
        client.loop.run_until_complete(start_coros(client))

if __name__ == '__main__':
    main()