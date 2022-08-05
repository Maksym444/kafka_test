from flask import Flask
from models import TgChannel

app = Flask(__name__)

def reset_channels():
    for rec in TgChannel.objects(locked=True, enabled=True):
        rec.locked = False
        rec.save()


@app.route('/')
def root():
    return "OK"


def main():
    reset_channels()
    app.run(debug=True, port=8080, host='0.0.0.0')

if __name__ == '__main__':
    main()