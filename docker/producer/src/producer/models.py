from asgiref.sync import sync_to_async
from django.db import models

# Create your models here.
class BaseModel(models.Model):
    class Meta:
        abstract = True

    create_date = models.DateTimeField(null=True, auto_now_add=True)
    last_update = models.DateTimeField(null=True, auto_now=True)

    @classmethod
    @sync_to_async
    def all(cls, ):
        return list(cls.objects.all())

    @classmethod
    @sync_to_async
    def update_by_filter(cls, filters, data):
        rec = cls.objects.filter(**filters)
        rec.update(**data)
        return list(rec)

    @classmethod
    @sync_to_async
    def upsert_by_filter(cls, filters, data):
        obj, created = cls.objects.get_or_create(
            defaults=data,
            **filters
        )
        return obj


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


    # uuid = models.UUIDField(default=generate_uuid, db_index=True, unique=True)
    # level = models.PositiveSmallIntegerField(
    #     choices=LEVEL_CHOICES.choices, default=LEVEL_CHOICES.MIDDLE
    # )
    # title = models.CharField(max_length=128)
    # description = models.TextField(max_length=1024, null=True, blank=True)  # noqa
    # image = models.ImageField(default="default.png", upload_to="covers")
    #
    # def __str__(self):
    #     return f"{self.title}"
    #
    # def questions_count(self):
    #     return self.questions.count()


class Channel(BaseModel):
    source = models.ForeignKey(Source, models.DO_NOTHING, blank=True, null=True)
    enabled = models.BooleanField(default=True)
    title = models.TextField(blank=True, null=True)
    url = models.TextField(db_index=True)
    channel_id = models.TextField(db_index=True, null=True)
    last_parsed = models.DateTimeField(null=True)
    last_message_id = models.IntegerField(default=0)
    last_message_ts = models.DateTimeField(null=True)


    # date = models.DateTimeField(blank=True, null=True)
    # username = models.TextField(blank=True, null=True)
    # node = models.ForeignKey(Node, models.DO_NOTHING, null=True)
    # channel_hash = models.TextField(null=True)
    # source_type = models.TextField(blank=True, null=True)
    # source_privacy = models.TextField(blank=True, null=True)
    # has_photo = models.BooleanField(null=True)
    # participants_count = models.BigIntegerField(blank=True, null=True)

    # class Meta:
    #     db_table = 'channel'

    def __str__(self):
        return f'id={self.id}, url={self.url}'
