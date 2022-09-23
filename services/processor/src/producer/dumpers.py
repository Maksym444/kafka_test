from abc import abstractmethod

from producer import models


class MsgDumper:
    @classmethod
    @abstractmethod
    async def dump(cls, msg):
        pass

    @classmethod
    def get_dumper(cls, type):
        """ Factory method that returns dumper for a given type """
        class_ = DUMP_TYPES.get(type)
        if class_ is None:
            raise RuntimeError(f"Unknown dumper type: {type}")

        return class_

    @classmethod
    def __call__(cls, type):
        return cls.get_dumper(cls, type)


class TgDumper(MsgDumper):

    def load_message(self):
        pass

    @classmethod
    async def dump(cls, msg):
        channel = await models.Channel.upsert_by_filter(
            filters={'url': msg['channel_url']},
            data={
                'url': msg['channel_url'],
                'last_message_id': msg['id'],
                'last_message_ts': msg['date'],
            }
        )
        return channel


class TwDumper(MsgDumper):

    def load_message(self):
        pass

    @classmethod
    async def dump(cls, msg):
        channel = await models.TwitterMessage.upsert_by_filter(
            filters={'user_id__user_id': msg['user_id']},
            data={
                'tweet_id': msg['tweet_id'],
                'date': msg['tweet_date'],
                'text': msg['tweet_text'],
            }
        )
        return channel


DUMP_TYPES = {
    "tg_message": TgDumper,
    "tw_message": TwDumper
}