import os

from api import app
from utils import reset_channels

MANAGER_RESTAPI_DEBUG = bool(os.getenv('MANAGER_RESTAPI_DEBUG')) or False
MANAGER_RESTAPI_PORT = int(os.getenv('MANAGER_RESTAPI_PORT', 8080))

def main():
    reset_channels()
    app.run(debug=MANAGER_RESTAPI_DEBUG, port=MANAGER_RESTAPI_PORT, host='0.0.0.0')


if __name__ == '__main__':
    main()