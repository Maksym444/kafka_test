import os
from pymongo import *

TWITTER_CONSUMER_KEY=os.getenv('TWITTER_CONSUMER_KEY')
TWITTER_CONSUMER_SECRET=os.getenv('TWITTER_CONSUMER_SECRET')
TWITTER_ACCESS_KEY=os.getenv('TWITTER_ACCESS_KEY')
TWITTER_ACCESS_SECRET=os.getenv('TWITTER_ACCESS_SECRET')

MONGO_HOST = os.getenv('MONGO_HOST')
MONGO_PORT = os.getenv('MONGO_PORT')
MONGO_DBNAME = os.getenv('MONGO_DBNAME')

# MongoDB host, db name, and collection names
# mng_cl = MongoClient('mongodb://localhost:27017/')
mng_cl = MongoClient(f'mongodb://{MONGO_HOST}:{MONGO_PORT}/')
# db = mng_cl['scrapper']
db = mng_cl[f'{MONGO_DBNAME}']
# user_collection = db['twitter_users_data']
tweets_collection = db['twitter_tweets_data']
sources_collection = db['sources']
# messages_collection = db['messages']

# # Twitter API access keys
consumer_key = TWITTER_CONSUMER_KEY
consumer_secret = TWITTER_CONSUMER_SECRET
access_key = TWITTER_ACCESS_KEY
access_secret = TWITTER_ACCESS_SECRET


# Local path to saved data(avatar and media)
path_to_files = '/mnt/data'
