import time
import asyncio
import os

# ----------------------------------------------------------------------------------------------------------------------
from pymongo import ReturnDocument

STARTUP_DELAY = 10
CONSUME_POLL_INTERVAL_SEC = 5
READ_TIMEOUT_SEC = 1
PARTITIONS_COUNT = int(os.getenv('KAFKA_PARTITIONS_NUM', 8))
FETCHER_SCALE_FACTOR = int(os.getenv('TELEGRAM_FETCHER_SCALE_FACTOR', 1))
SIZE_KB = 1024
SIZE_MB = SIZE_KB*SIZE_KB
KAFKA_HOST = os.getenv('KAFKA_HOST')
KAFKA_PORT = os.getenv('KAFKA_PORT')
# from ..models import TgChannel
import os

from mongoengine import *
# from motorengine import *

from pytest_mongo import factories
# from pytest_mock_resources import create_mongo_fixture

MONGO_HOST = os.getenv('MONGO_HOST')
MONGO_PORT = int(os.getenv('MONGO_PORT'))
MONGO_DBNAME = os.getenv('MONGO_DBNAME')

# connect('mongodb')
# mongo_connection_uri = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/{MONGO_DBNAME}"
# connect(host=mongo_connection_uri)


# connect('mongodb')
test_mongo = factories.mongo_proc(host=MONGO_HOST, port=MONGO_PORT)
mongo_my = factories.mongodb('test_mongo')
connect(db='test_mongo', host=MONGO_HOST, port=MONGO_PORT)
# mongo = create_mongo_fixture()

class TgChannelTest(Document):
    locked = IntField(default=0)

    def __str__(self):
        return f'locked={self.locked}'


async def consumer(partition_id):
    for _ in range(100):
        # qs = TgChannelTest.objects(locked=0)
        # if qs:
        #     time.sleep(0.001)
        #     rec = list(qs)[0]
        #     rec.locked = 1
        #     rec.save()
        #     print(f'AFTER [{partition_id}]:', type(rec), rec)

        # channel_dict = TgChannelTest._get_collection().find_one_and_update(
        #     filter={'locked': 0},
        #     update={'$inc': {'locked': 1}},
        #     return_document=ReturnDocument.AFTER
        # )
        channel_dict = TgChannelTest._get_collection().find_one_and_update(
            filter={'locked': 1},
            update={'$inc': {'locked': -1}},
            return_document=ReturnDocument.AFTER
        )

async def start_coros():
    consumers = [consumer(i) for i in range(PARTITIONS_COUNT//FETCHER_SCALE_FACTOR)]
    await asyncio.gather(*consumers)


def test_main():
    # print('test_main: ', mongo)
    # TgChannelTest.objects.delete()
    # for _ in range(100):
    #     TgChannelTest(locked=0).save()
    # for rec in TgChannelTest.objects.all():
    #     rec.locked = 0
    #     rec.save()

    asyncio.run(start_coros())

    print([rec.locked for rec in TgChannelTest.objects.all()])
    print('---TgChannelTest.objects.all()---')
    for rec in TgChannelTest.objects.all():
        assert rec.locked <= 1
