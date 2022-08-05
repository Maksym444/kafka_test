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
        return f'id={self.id}, url={self.url}'
