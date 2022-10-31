import os
import logging

from api import app

SEARCHER_RESTAPI_DEBUG = bool(os.getenv('SEARCHER_RESTAPI_DEBUG')) or False
SEARCHER_RESTAPI_PORT = int(os.getenv('SEARCHER_RESTAPI_PORT', 8080))

logging.basicConfig(level=logging.INFO)


def main():
    app.run(debug=SEARCHER_RESTAPI_DEBUG, port=SEARCHER_RESTAPI_PORT, host='0.0.0.0')


if __name__ == '__main__':
    main()