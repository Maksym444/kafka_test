from models import TgChannel


def reset_channels():
    for rec in TgChannel.objects(locked=True, enabled=True):
        rec.locked = False
        rec.save()