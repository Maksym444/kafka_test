from flask import Flask
from marshmallow import validate
from telemongo import MongoSession
from telethon import TelegramClient
from webargs import fields
from webargs.flaskparser import use_kwargs

from models import TgChannel, TgAccountInfo, mongo_connection_base_uri

g_client = None
app = Flask(__name__)

def reset_channels():
    for rec in TgChannel.objects(locked=True, enabled=True):
        rec.locked = False
        rec.save()

def phone_validator(value):
    #TODO: validate phonenumber
    return value


async def request_auth(client, phone):
    if not client.is_connected():
        await client.connect()
    me = await client.get_me()
    if me is None:
        await client.send_code_request(phone, force_sms=False)
    return me

async def confirm_auth(client, phone, auth_code):
    me = await client.sign_in(phone, code=auth_code)
    return me


@app.route('/')
def root():
    return "OK"


@app.route('/accounts/register', methods=['GET'])
@use_kwargs(
    {
        "phone": fields.Str(
            required=True,
            validate=[phone_validator]
            # validate=[validate.Length(min=2, max=6)],
        ),
        "app_id": fields.Integer(
            required=True
        )
    },
    location="query",
)
def accounts_register(phone, app_id):
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

    result = g_client.loop.run_until_complete(request_auth(g_client, phone))

    if result is None:
        return "Auth code is requested"
    else:
        return "Already authorized"


@app.route('/accounts/register_auth_code', methods=['POST'])
@use_kwargs(
    {
        "phone": fields.Str(
            required=True,
            validate=[phone_validator]
        ),
        "auth_code": fields.Integer(
            required=True,
            validate=[validate.Range(min=10000, max=99999)]
        )
    },
    location="query",
)
def accounts_auth_code(phone, auth_code):
    global g_client
    if g_client is None:
        return "Auth code is not yet requested", 405
    result = g_client.loop.run_until_complete(confirm_auth(g_client, phone, auth_code))
    g_client = None
    return f"Successfully authorised: {result}"


def main():
    reset_channels()
    app.run(debug=True, port=8080, host='0.0.0.0')

if __name__ == '__main__':
    main()