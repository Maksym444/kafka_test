from mongoengine import *

# connect('mongodb')
connect(host="mongodb://mongodb:27017/fetcher")


class TgChannel(Document):
    url = StringField(required=True)
    enabled = BooleanField(default=True)
    locked = BooleanField(default=False)
    title = StringField(max_length=150)
    channel_id = StringField(db_index=True)
    last_parsed = DateTimeField(null=True)
    last_message_id = IntField(default=0)
    last_message_ts = DateTimeField(null=True)


class TgAccount(Document):
    db_name = StringField(required=True, unique=True)
    locked = BooleanField(default=False)
    app_id = IntField(required=True)
    app_secret = StringField(required=True)
