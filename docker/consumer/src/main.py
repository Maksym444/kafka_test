import datetime
import random
import asyncio
import json
import os
import re
import time
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from pymongo import ReturnDocument
from telethon.errors import FloodWaitError

import parser
from logger import logger
from models import TgAccount, TgChannel, mongo_connection_uri

from telethon import TelegramClient
from telemongo import MongoSession

STARTUP_DELAY = 20
CONSUME_POLL_INTERVAL_SEC = 5
READ_TIMEOUT_SEC = 1
PARTITIONS_COUNT = int(os.getenv('KAFKA_PARTITIONS_NUM', 8))
SIZE_KB = 1024
SIZE_MB = SIZE_KB*SIZE_KB
KAFKA_HOST = os.getenv('KAFKA_HOST')
KAFKA_PORT = os.getenv('KAFKA_PORT')
CONSUMER_SCALE_FACTOR = int(os.getenv('CONSUMER_SCALE_FACTOR'))
tg_account = None
# TG_ERROR_MISSING_CHANNEL = 'Cannot find any entity corresponding to'
TG_CHANNEL_ERRORS = [
    'Nobody is using this username, or the username is unacceptable. If the latter, it must match.*',
    'Cannot find any entity corresponding to.*',
    'No user has ".*" as username',
    'The channel specified is private and you lack permission to access it.*'
]


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
            sort=[('last_parsed', 1)],
            return_document=ReturnDocument.AFTER
        )

        if channel_dict is None:
            raise RuntimeError('Couldn\'t find available TG channel!')

        channel=TgChannel.objects(url=channel_dict['url']).first()
        if not channel.channel_id:
            channel_info = await parser.get_channel_info(client, channel.url)
            channel.channel_id = channel_info.id
            channel.save()

        logger.info(f'PARTITION_ID {partition_id}: picked up channel: %s, last_message_ts=%s, last_parsed=%s',
                    channel.url, channel.last_message_ts, channel.last_parsed)

        try:
            async for msg in parser.get_messages(client, channel.url, channel.channel_id, channel.last_message_id):
                # await kafka_producer.send_and_wait("topic_result", json.dumps(msg).encode(), partition=partition_id)
                date_raw = msg.pop('date_raw')
                await kafka_producer.send_and_wait("topic_result", json.dumps(msg).encode(), partition=partition_id)
                logger.info(f'PARTITION_ID {partition_id}: Replied with msg={msg}')
                channel.last_message_id = msg['id']
                channel.last_message_ts = date_raw
                channel.last_parsed = (datetime.datetime.now())
                channel.save()

        except FloodWaitError as ex:
            # time.sleep(ex.seconds)
            logger.error('EXCEPTION (FloodWaitError): %s', ex)

        except Exception as ex:
            if channel:
                for error in TG_CHANNEL_ERRORS:
                    if re.match(error, str(ex)):
                        channel.enabled = False
                        channel.save()

            logger.error('EXCEPTION: %s', ex)

        finally:
            logger.info(f'PARTITION_ID {partition_id}: Sleeping till the next attempt...')
            channel.locked = False
            channel.last_parsed = (datetime.datetime.now())
            channel.save()
            await asyncio.sleep(CONSUME_POLL_INTERVAL_SEC)


async def start_coros(client):
    # consumers = [consumer(i) for i in range(PARTITIONS_COUNT//2)]
    producers = [producer(i, client) for i in range(PARTITIONS_COUNT//CONSUMER_SCALE_FACTOR)]
    await asyncio.gather(*producers, loop=client.loop)


def main():
    logger.info(f'CONSUMER: wait until broker is up and running {STARTUP_DELAY}...')
    time.sleep(random.randint(STARTUP_DELAY, STARTUP_DELAY))

    tg_account = TgAccount._get_collection().find_one_and_update(
        filter={'locked': False},
        update={'$set': {'locked': True}},
        return_document = ReturnDocument.AFTER
    )

    if tg_account is None:
        raise RuntimeError('Coudln\'t find available TG account!')

    # tg_account = TgAccount.objects(db_name='memory2_1').first()
    #
    # session = MongoSession('fetcher', host=mongo_connection_uri)

    client = TelegramClient(
        session=tg_account['db_name'],
        # session=session,
        api_id=tg_account['app_id'],
        api_hash=tg_account['app_secret']
    )

    with client:
        logger.info('CONSUMER: start reading messages!')
        # parser.client.loop.run_until_complete(consumer(0))
        client.loop.run_until_complete(start_coros(client))

if __name__ == '__main__':
    main()