from asgiref.sync import sync_to_async
from django.db import models
from django.db import transaction

class BaseModel(models.Model):
    class Meta:
        abstract = True

    create_date = models.DateTimeField(null=True, auto_now_add=True)
    last_update = models.DateTimeField(null=True, auto_now=True)

    @classmethod
    @sync_to_async
    def all(cls):
        return list(cls.objects.all())

    @classmethod
    @sync_to_async
    def update_by_filter(cls, filters, data):
        rec = cls.objects.filter(**filters)
        rec.update(**data)
        return list(rec)

    @classmethod
    @sync_to_async
    @transaction.atomic
    def upsert_by_filter(cls, filters, data):
        obj, created = cls.objects.get_or_create(
            defaults=data,
            **filters
        )
        if not created:
            for key, value in data.items():
                setattr(obj, key, value)
            obj.save()
        return obj

    @classmethod
    @sync_to_async
    def create_record(cls, data):
        rec = cls.objects.create(**data)
        return rec


class Source(BaseModel):
    # class TYPES(models.IntegerChoices):  # noqa:
    #     TELEGRAM = 0, "Telegram"
    #     TWITTER = 1, "Twitter"
    #
    # enabled = models.BooleanField()
    # last_parsed = models.DateTimeField(null=True)
    # source_type = models.PositiveSmallIntegerField(
    #     choices=TYPES.choices, default=TYPES.TELEGRAM
    # )
    name = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'producer_source'


class Channel(BaseModel):
    source = models.ForeignKey(Source, models.DO_NOTHING, blank=True, null=True)
    enabled = models.BooleanField(default=True)
    title = models.TextField(blank=True, null=True)
    url = models.TextField(db_index=True)
    channel_id = models.TextField(db_index=True, null=True)
    last_parsed = models.DateTimeField(null=True)
    last_message_id = models.IntegerField(default=0)
    last_message_ts = models.DateTimeField(null=True)

    def __str__(self):
        return f'id={self.id}, url={self.url}, last_message_id={self.last_message_id}'

    class Meta:
        db_table = 'producer_channel'


class ChannelUsers(BaseModel):
    bot = models.TextField(blank=True, null=True)
    user_id = models.BigIntegerField()
    first_name = models.TextField(blank=True, null=True)
    last_name = models.TextField(blank=True, null=True)
    username = models.TextField(blank=True, null=True)
    phone = models.TextField(blank=True, null=True)
    photo = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'channel_users'



class Messages(BaseModel):
    messages_id = models.TextField(blank=True, null=True, db_index=True)
    date = models.DateTimeField(blank=True, null=True)
    message_text = models.TextField(blank=True, null=True)
    message_attachments = models.TextField(blank=True, null=True)
    channel = models.ForeignKey(Channel, models.DO_NOTHING, blank=True, null=True)
    category = models.TextField(blank=True, null=True)
    user = models.ForeignKey(ChannelUsers, models.DO_NOTHING, blank=True, null=True)
    source_type = models.TextField(blank=True, null=True)
    user_avatar = models.TextField(blank=True, null=True)
    message_type = models.TextField(blank=True, null=True)
    has_media = models.BooleanField(blank=True, null=True)
    has_replies = models.BooleanField(blank=True, null=True)

    class Meta:
        db_table = 'messages'
#
#     @classmethod
#     def find_message_by_id(cls, id, channel_id):
#         records = cls.objects.filter(messages_id=id, channel__channel_id=channel_id)
#         if records:
#             return records
#         return None
#
#     @classmethod
#     def count_by_word(cls, word, start, end, category, tags, source_type):
#         params = dict(
#             message_text__icontains=word,
#             date__range=(start, end),
#             category__in=category,
#             # source_type__in=source_type
#         )
#         if tags:
#             params.update(dict(channel__tags__in=tags))
#
#         num_records = cls.objects.filter(**params).count()
#
#         return num_records
#
#     @classmethod
#     def find_message_by_word(cls, word, start, end, category, tags, source_type, page, page_size):
#         params = dict(
#             message_text__icontains=word,
#             date__range=(start, end),
#             category__in=category,
#             # source_type__in=source_type
#         )
#         if tags:
#             params.update(dict(channel__tags__in=tags))
#
#         records = cls.objects.filter(**params).\
#                     select_related('channel', 'user').\
#                     order_by('date')
#
#         return records[(page-1)*page_size: page*page_size]
#
#     @classmethod
#     def create_record(cls, data):
#         rec = cls.objects.create(**data)
#         return rec
#
#
# class Replies(models.Model):
#     message_text = models.TextField(blank=True, null=True)
#     message_attachments = models.TextField(blank=True, null=True)
#     reply_to = models.ForeignKey(Messages, models.DO_NOTHING, blank=True, null=True)
#     date = models.DateTimeField(blank=True, null=True)
#     user = models.ForeignKey(ChannelUsers, models.DO_NOTHING, blank=True, null=True)
#     user_avatar = models.TextField(blank=True, null=True)
#     has_media = models.BooleanField(blank=True, null=True)
#     type = models.TextField(blank=True, null=True)
#
#     class Meta:
#         db_table = 'replies'
#
#     @classmethod
#     def create_record(cls, data):
#         rec = cls.objects.create(**data)
#         return rec
#
#     @classmethod
#     def find_replies_by_message(cls, message):
#         records = cls.objects.filter(reply_to=message)
#         if records:
#             return records
#         return None
#
#     @classmethod
#     def count_by_word(cls, word, start, end, category, tags, source_type):
#         params = dict(
#             message_text__icontains=word,
#             date__range=(start, end),
#             reply_to__category__in=category,
#             # reply_to__source_type__in=source_type
#         )
#         if tags:
#             params.update(dict(reply_to__channel__tags=tags))
#
#         num_records = cls.objects.filter(**params).count()
#
#         return num_records
#
#     @classmethod
#     def find_reply_by_word(cls, word, start, end, category, tags, source_type, page, page_size):
#         params = dict(
#             message_text__icontains=word,
#             date__range=(start, end),
#             reply_to__category__in=category,
#             # reply_to__source_type__in=source_type
#         )
#
#         if tags:
#             params.update(dict(reply_to__channel__tags=tags))
#
#         records = cls.objects.\
#                     filter(**params).\
#                     select_related('reply_to', 'reply_to__channel', 'user').\
#                     order_by('date')
#
#         return records[(page-1)*page_size: page*page_size]
#


class TwitterSource(BaseModel):
    source = models.ForeignKey(Source, models.DO_NOTHING, blank=True, null=True)
    user_id = models.TextField(db_index=True)
    has_photo = models.BooleanField()
    channel_about = models.TextField(null=True)
    channel_title = models.TextField(null=True)
    creation_date = models.DateTimeField(null=True)
    followers = models.IntegerField(null=True)
    location = models.TextField(null=True)

    class Meta:
        db_table = 'twitter_source'


class TwitterMessage(BaseModel):
    user_id = models.ForeignKey(TwitterSource, models.DO_NOTHING, blank=True, null=True)
    tweet_id = models.TextField()
    date = models.DateTimeField(null=True)
    text = models.TextField(null=True)
    retweet = models.IntegerField(null=True)
    likes = models.IntegerField(null=True)
    location = models.TextField(null=True)
    source_type = models.TextField(blank=True, null=True)
    has_media = models.BooleanField(null=True)
    media = models.TextField(blank=True, null=True)
    is_quote = models.BooleanField(null=True)
    quote_id = models.TextField(null=True)
    participants_count = models.BigIntegerField(blank=True, null=True)
    tags = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'twitter_message'

