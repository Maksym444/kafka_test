from flask import Flask, jsonify
from marshmallow import validate

from webargs import fields
from webargs.flaskparser import use_kwargs

from telethon_funcs import phone_validator, loop, request_auth, confirm_auth, reset_channels

app = Flask(__name__)


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
    result = loop.run_until_complete(request_auth(app_id, phone))

    if result is None:
        return "Auth code is requested"
    else:
        return "Already authorized!"


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
        )
    },
    location="json",
)
def accounts_auth_code(phone, auth_code):
    result = loop.run_until_complete(confirm_auth(phone, auth_code))
    return f"Successfully authorised: {result}"


def main():
    reset_channels()
    app.run(debug=True, port=8080, host='0.0.0.0')

if __name__ == '__main__':
    main()