import asyncio
import datetime
import time
import json
import os
import random
import re

from aiokafka import AIOKafkaProducer
from pymongo import ReturnDocument
from telemongo import MongoSession
from telethon import TelegramClient
from telethon.errors import FloodWaitError

import parser
from logger import logger
from models import TgChannel, mongo_connection_base_uri, TgAccountInfo

STARTUP_DELAY = 20
CONSUMER_POLL_INTERVAL_SEC = 5
SIZE_KB = 1024
SIZE_MB = SIZE_KB*SIZE_KB
TG_CHANNEL_ERRORS = [
    'Nobody is using this username, or the username is unacceptable. If the latter, it must match.*',
    'Cannot find any entity corresponding to.*',
    'No user has ".*" as username',
    'The channel specified is private and you lack permission to access it.*'
]

TELETHON_FETCH_MSG_COUNT = int(os.getenv('TELETHON_FETCH_MSG_COUNT', 0)) or None
PARTITIONS_COUNT = int(os.getenv('KAFKA_PARTITIONS_NUM', 8))
KAFKA_HOST = os.getenv('KAFKA_HOST')
KAFKA_PORT = os.getenv('KAFKA_PORT')


async def consumer(partition_id, client):
    """
        Consumer coroutine
    :param partition_id: Partition id
    :param client: Telegram client
    :return:
    """
    kafka_producer = AIOKafkaProducer(
        bootstrap_servers=f'{KAFKA_HOST}:{KAFKA_PORT}',
        max_request_size=5*SIZE_MB
    )

    await kafka_producer.start()

    while True:
        # atomic read+update (CAS-like operation)
        channel_dict = TgChannel._get_collection().find_one_and_update(
            filter={'locked': False, 'enabled': True, '$or': [{'app_id': client.api_id}, {'app_id': None}]},
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
            async for msg in parser.get_messages(client, channel.url, channel.channel_id, channel.last_message_id,
                                                 limit=TELETHON_FETCH_MSG_COUNT):
                date_raw = msg.pop('date_raw')
                await kafka_producer.send_and_wait("topic_result", json.dumps(msg).encode(), partition=partition_id)
                logger.info(f'PARTITION_ID {partition_id}: Replied with msg={msg}')
                channel.last_message_id = msg['id']
                channel.last_message_ts = date_raw
                channel.last_parsed = (datetime.datetime.now())
                channel.save()

        except FloodWaitError as ex:
            # time.sleep(ex.seconds)
            logger.error('EXCEPTION (FloodWaitError): %s, %d', ex, ex.seconds)

        except Exception as ex:
            if channel:
                for error in TG_CHANNEL_ERRORS:
                    if re.match(error, str(ex)):
                        channel.enabled = False
                        channel.save()
                        break

            logger.error('EXCEPTION: ex=%s, url=%s, last_id=%s, partition=%s',
                         ex, channel.url, channel.last_message_id, partition_id)
            # raise ex

        finally:
            logger.info(f'PARTITION_ID {partition_id}: Sleeping till the next attempt...')
            channel.locked = False
            channel.last_parsed = (datetime.datetime.now())
            channel.save()
            await asyncio.sleep(CONSUMER_POLL_INTERVAL_SEC)


async def start_coros(client):
    """
        Start coroutines
    :param client: Telegram client
    :return:
    """
    consumers = [consumer(i, client) for i in range(PARTITIONS_COUNT)]
    await asyncio.gather(*consumers, loop=client.loop)


def main():
    """
        Main function
    :return:
    """
    logger.info(f'CONSUMER: wait until broker is up and running {STARTUP_DELAY}...')
    time.sleep(random.randint(STARTUP_DELAY, STARTUP_DELAY))

    tg_account = TgAccountInfo.objects.order_by('last_access_ts').first()

    if tg_account is None:
        raise RuntimeError('Coudn\'t find available TG account!')

    tg_account.last_access_ts = datetime.datetime.now()
    tg_account.save()

    session = MongoSession(
        database=f'account_{tg_account.app_id}',
        host=f'{mongo_connection_base_uri}/account_{tg_account.app_id}'
    )

    client = TelegramClient(
        session=session,
        api_id=tg_account.app_id,
        api_hash=tg_account.app_secret
    )

    with client:
        logger.info('CONSUMER: start reading messages!')
        client.loop.run_until_complete(start_coros(client))


# ----------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    main()