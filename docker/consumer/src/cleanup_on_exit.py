from models import TgChannel, TgAccount


def reset_channels():
    for rec in TgChannel.objects(locked=True, enabled=True):
        rec.locked = False
        rec.save()

    for rec in TgAccount.objects(locked=True):
        rec.locked = False
        rec.save()

    TgAccount(
        locked=False,
        db_name='CLENAUP',
        app_id='app_id',
        app_secret='42'
    ).save()

if __name__ == '__main__':
    reset_channels()