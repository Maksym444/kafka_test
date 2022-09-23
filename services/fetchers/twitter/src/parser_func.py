import json

import os
import time
import uuid

import requests
import tweepy
from datetime import timedelta
from tweepy import OAuthHandler
from config import consumer_key, consumer_secret, path_to_files
from db_mongo_funcs import save_user_to_mongo, save_tweets_to_mongo, check_user_avatar, \
    get_last_publ_from_mongodb, get_accounts_to_parse
import logging

from kafka import KafkaProducer

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                    level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')


KAFKA_HOST = os.getenv('KAFKA_HOST')
KAFKA_PORT = os.getenv('KAFKA_PORT')


# Main logic for script, with all checks to proper work and saving resources(requests count)
# Getting twitter id, and calling one by one methods and functions to parse user or stop working
# if nothing to parse or something is wrong with added information.
def parsing():
    # Get accounts to work on from database. Account must be enabled and type must be Twitter
    sources = get_accounts_to_parse()
    parser = TweetParser()
    for source in sources:
        account = source["UserID"]
        category = source["Category"]
        time.sleep(3)
        try:
            parser.fetch_user(account)
        except Exception as e:
            logging_info = f"The exception is following: {e}"
            logging.info(logging_info)
        last_id = get_last_publ_from_mongodb(account)
        # If it is the first time fetching user's info.
        if last_id is None:
            try:
                parser.fetching_tweets(account, category, limit=500)
                logging_info = f'{account} has been scraped for the first time.'
                logging.info(logging_info)
                # return True
            except Exception as e:
                logging_info = f"The exception is following:{e}"
                logging.info(logging_info)
        else:
            try:
                parser.update_fetch(account, category, last_id)
                logging_info = f'{account} has been updated.'
                logging.info(logging_info)
            except Exception as e:
                logging_info = 'There is something wrong or there is nothing to parse! ' \
                               f'Check twitter id: {account}.The exception is following:{e}'
                logging.info(logging_info)

        logging_info = 'The cycle is complete. Waiting 2 min for the next loop.'
        logging.info(logging_info)
        # time.sleep(120)
        time.sleep(10)


# Getting avatar of the user and saving it locally(for fetch_user)
def get_user_avatar(avatar_url, account):
    filename = f"{path_to_files}/avatars/{account}.jpg"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    response = requests.get(avatar_url)
    file = open(filename, "wb")
    file.write(response.content)
    file.close()
    return filename


# Getting media of the tweet and saving it locally
def process_tweet_media(tweet, user_id):
    try:
        extended = tweet.extended_entities
        rv = []
        if not extended:
            return None
        if "media" in extended:
            try:
                path = f"{path_to_files}/{user_id}"
                os.mkdir(path)
            except OSError:
                pass
            for x in extended["media"]:
                if x["type"] == "photo":
                    url = x["media_url"]
                    logging_info = f'Downloading media from: {url}'
                    logging.info(logging_info)
                    filename = f"{path_to_files}/{user_id}/{uuid.uuid4().hex}.jpg"
                    response = requests.get(url)
                    open(filename, "wb").write(response.content)
                    rv.append(filename)
                elif x["type"] in ["video", "animated_gif"]:
                    variants = x["video_info"]["variants"]
                    variants.sort(key=lambda a: a.get("bitrate", 0))
                    url = variants[-1]["url"].rsplit("?tag")[0]
                    logging_info = f'Downloading media from: {url}'
                    logging.info(logging_info)
                    filename = f"{path_to_files}/{user_id}/{uuid.uuid4().hex}.mp4"
                    response = requests.get(url)
                    open(filename, "wb").write(response.content)
                    rv.append(filename)
        return rv
    except Exception:
        return None


class TweetParser(object):
    def __init__(self):
        self.api = None
        auth = OAuthHandler(consumer_key, consumer_secret)
        self.api = tweepy.API(auth, wait_on_rate_limit_notify=True, wait_on_rate_limit=True,)
        self.producer = KafkaProducer(bootstrap_servers=f'{KAFKA_HOST}:{KAFKA_PORT}')

        # wait_on_rate_limit make the rest of the code wait until update of the rate limit.

    # After the first check we should use update_fetch to get new tweets.
    # Give to it a user to check, all data will be placed in db.
    def update_fetch(self, account, category, last_id):
        self.fetching_tweets(account, category, last_id)

    # Func for the first check user base information presented on user's twitter account
    def fetch_user(self, account):
        if check_user_avatar(account):
            logging_info = f'{account} is already existing in db.'
            logging.info(logging_info)
            return
        else:
            api = self.api
            twitter_user = api.get_user(account)
            username = twitter_user.screen_name
            followers_count = twitter_user.followers_count
            registration_date = twitter_user.created_at
            location = twitter_user.location
            if location == '':
                location = 'No location data'
            avatar_url = twitter_user.profile_image_url
            avatar = get_user_avatar(avatar_url, account)
            title = twitter_user.name
            about = twitter_user.description
            # Saving all data to mongo
            save_user_to_mongo(avatar, username, followers_count, location, registration_date, account, title, about)

    # Fetching users tweets media(send account name as a param), and saving it in list(so far), then send to db.
    def fetching_tweets(self, account, category, last_id=None, tweet_mode='extended', limit=3250):
        api = self.api
        count = 1
        list_of_tweets = list()
        flag_tweet = last_id
        for tweet in tweepy.Cursor(api.user_timeline, id=account,
                                   since_id=last_id, tweet_mode=tweet_mode).items(limit):
            temp = dict()
            media_urls = process_tweet_media(tweet, account)
            tweet_id = tweet.id_str
            tweet_date = tweet.created_at + timedelta(hours=2)
            tweet_text = tweet.full_text
            location = tweet.user.location
            retweet_count = tweet.retweet_count
            likes_count = tweet.favorite_count
            if location == '':
                location = 'No location data'
            temp['user_id'] = account
            temp['tweet_id'] = tweet_id
            # temp['tweet_date'] = tweet_date
            temp['tweet_date'] = str(tweet_date)
            temp['tweet_text'] = tweet_text
            temp['location'] = location
            temp['retweet_count'] = retweet_count
            temp['likes_count'] = likes_count
            temp['category'] = category
            temp['is_quote'] = tweet.is_quote_status
            try:
                if tweet.is_quote_status:
                    temp['quote_id'] = tweet.quoted_status_id_str
                else:
                    temp['quote_id'] = None
            except AttributeError:
                temp['quote_id'] = None
            # Media
            try:
                if media_urls is None:
                    temp['media'] = None
                    temp['has_media'] = False
                else:
                    temp['media'] = media_urls
                    temp['has_media'] = True
            except Exception as e:
                logging_info = f'Error with media: {e}, tweet id: {tweet_id}, {account}'
                logging.info(logging_info)
            list_of_tweets.append(temp)
            logging_info = f'Tweet: {count}'
            logging.info(logging_info)
            if count == 1:
                flag_tweet = tweet_id
            count += 1

            temp['type'] = 'tw_message'
            self.producer.send('topic_result', json.dumps(temp).encode('utf-8'))

        save_tweets_to_mongo(list_of_tweets, flag_tweet, account)
