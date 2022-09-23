import os
from mongoengine import *

MONGO_HOST = os.getenv('MONGO_HOST')
MONGO_PORT = os.getenv('MONGO_PORT')
MONGO_DBNAME = os.getenv('MONGO_DBNAME')

mongo_connection_base_uri = f"mongodb://{MONGO_HOST}:{MONGO_PORT}"
mongo_connection_uri = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/{MONGO_DBNAME}"
connect(host=mongo_connection_uri)


class TgAccountInfo(Document):
    db_name = StringField(required=True, unique=True)
    app_id = IntField(required=True)
    app_secret = StringField(required=True)
    last_access_ts = DateTimeField(null=True)


class TgChannel(Document):
    url = StringField(required=True)
    enabled = BooleanField(default=True)
    locked = BooleanField(default=False)
    title = StringField(max_length=150)
    channel_id = StringField(db_index=True)
    last_parsed = DateTimeField(null=True)
    last_message_id = IntField(default=0)
    last_message_ts = DateTimeField(null=True)
    app_id = IntField(required=False)
