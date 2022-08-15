import asyncio

from telemongo import MongoSession
from telethon import TelegramClient

from models import TgChannel, TgAccountInfo, mongo_connection_base_uri

g_client = None
loop = asyncio.get_event_loop()


def reset_channels():
    for rec in TgChannel.objects(locked=True, enabled=True):
        rec.locked = False
        rec.save()


def phone_validator(value):
    #TODO: validate phonenumber
    return value


async def request_auth(app_id, phone):
    global g_client

    tg_account = TgAccountInfo.objects(app_id=app_id).first()

    session = MongoSession(
        database=f'account_{tg_account.app_id}',
        host=f'{mongo_connection_base_uri}/account_{tg_account.app_id}'
    )

    g_client = TelegramClient(
        session=session,
        api_id=tg_account.app_id,
        api_hash=tg_account.app_secret
    )

    if not g_client.is_connected():
        await g_client.connect()
    me = await g_client.get_me()
    if me is None:
        await g_client.send_code_request(phone, force_sms=False)
    return me


async def confirm_auth(phone, auth_code):
    global g_client
    if g_client is None:
        return "Auth code is not yet requested", 405
    me = await g_client.sign_in(phone, code=auth_code)
    g_client = None
    return me
