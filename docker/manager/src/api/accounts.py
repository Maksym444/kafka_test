import asyncio

from telemongo import MongoSession
from telethon import TelegramClient, errors

from models import TgAccountInfo, mongo_connection_base_uri

g_client = None
loop = asyncio.get_event_loop()


def request_auth(app_id, phone):
    async def request_auth_async(app_id, phone):
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

    result = loop.run_until_complete(request_auth_async(app_id, phone))

    if result is None:
        return "Auth code is requested"
    else:
        return "Already authorized!"


def confirm_auth(phone, auth_code, password):
    async def confirm_auth_async(phone, auth_code, password):
        global g_client
        if g_client is None:
            return "Auth code is not yet requested", 405
        try:
            me = await g_client.sign_in(phone, code=auth_code)
        except errors.SessionPasswordNeededError:
            me = await g_client.sign_in(phone, password=password)
        g_client = None
        return me

    result = loop.run_until_complete(confirm_auth_async(phone, auth_code, password))
    return f"Successfully authorised: {result}"