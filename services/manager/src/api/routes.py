from flask import jsonify
from marshmallow import validate
from webargs import fields
from webargs.flaskparser import use_kwargs

from validators import phone_validator
from .accounts import request_auth, confirm_auth
from .server import app


@app.errorhandler(422)
@app.errorhandler(400)
def handle_error(err):
    headers = err.data.get("headers", None)
    messages = err.data.get("messages", ["Invalid request."])
    result = [
        jsonify({
            "Description": err.description,
            "Code": err.code,
            "Errors": messages
        }),
        err.code
    ]
    if headers:
        return result.append(headers)

    return tuple(result)


@app.route('/')
def root():
    return "OK"


@app.route('/accounts/register', methods=['GET'])
@use_kwargs(
    {
        "app_id": fields.Integer(
            required=True
        ),
        "phone": fields.Str(
            required=True,
            validate=[phone_validator]
        )
    },
    location="query",
)
def accounts_register(app_id, phone):
    return request_auth(app_id, phone)


@app.route('/accounts/auth_code', methods=['POST'])
@use_kwargs(
    {
        "phone": fields.Str(
            required=True,
            validate=[phone_validator]
        ),
        "auth_code": fields.Integer(
            required=True,
            validate=[validate.Range(min=10000, max=99999)]
        ),
        "password": fields.Str(
            required=False,
            missing=''
        ),

    },
    location="json",
)
def accounts_auth_code(phone, auth_code, password):
    return confirm_auth(phone, auth_code, password)
