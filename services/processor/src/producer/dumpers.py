from abc import abstractmethod

from producer import models

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

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
        message = await models.Messages.create_record(
            data={
                'messages_id': msg['id'],
                # 'date': msg['date_raw'],
                'date': msg['date'],
                'message_text': msg['message'],
                'user_avatar': msg.get('user_avatar'),
                'channel': channel,
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


class EsDumper(MsgDumper):

    es = Elasticsearch(["http://elasticsearch:9200"])
    INDEX_NAME = 'messages'

    def load_message(self):
        pass

    @classmethod
    async def create_index(cls):
        """Check if index exists and create it if not"""
        if not cls.es.indices.exists(index=cls.INDEX_NAME):
            cls.es.indices.delete(index=cls.INDEX_NAME, ignore=404)
            cls.es.indices.create(
                index=cls.INDEX_NAME,
                body={
                    'mappings': {
                        # DOC_TYPE: {                                   # This mapping applies to products.
                        'properties': {  # Just a magic word.
                            'message': {  # The field we want to configure.
                                'type': 'text',  # The kind of data we’re working with.
                                'fields': {  # create an analyzed field.
                                    'russian_analyzed': {  # Name that field `name.english_analyzed`.
                                        'type': 'text',  # It’s also text.
                                        # 'analyzer': 'english',              # And here’s the analyzer we want to use.
                                        'analyzer': 'custom_russian_analyzer',  # And here’s the analyzer we want to use.
                                    }
                                }
                            },
                        }
                        # }
                    },
                    'settings': {
                        'analysis': {  # magic word.
                            'analyzer': {  # yet another magic word.
                                'custom_russian_analyzer': {  # The name of our analyzer.
                                    'type': 'russian',  # The built in analyzer we’re building on.
                                    'stopwords': ['made', '_russian_'],  # Our custom stop words, plus the defaults.
                                }
                            }
                        }
                    }
                }
            )

    @classmethod
    async def dump(cls, msg):

        await cls.create_index()

        message = cls.es.create(
            index=cls.INDEX_NAME,
            # doc_type=DOC_TYPE,
            # id=1,
            id=msg['id'],
            body={
                "message": msg['message'],
                "id": msg['id'],
                "image": msg.get('user_avatar'),
                "date": msg['date'],
                "channel": msg['channel_url'],
            }
        )
        return message


DUMP_TYPES = {
    "tg_message": TgDumper,
    "tw_message": TwDumper
}
