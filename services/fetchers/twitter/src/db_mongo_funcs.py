from config import tweets_collection, sources_collection
import logging
from datetime import datetime

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                    level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')


# Get users to parse from database
def get_accounts_to_parse():
    sources = sources_collection.find({"Enabled": True, "SourceType": "twitter"}, no_cursor_timeout=True)
    return sources


# Check whether user exists in database. Return True if so:
def check_user_avatar(account):
    user_doc = sources_collection.find_one({'UserID': account}, {'HasPhoto': 1, '_id': 0})
    try:
        result = user_doc['HasPhoto']
    except Exception as e:
        logging.info(e)
        result = None
    return result


# Saving user data from fetcher to db
# Receive all user's general information, such as
def save_user_to_mongo(avatar, username, followers_count, location, registration_date, account, title, about):
    if avatar is not None:
        sources_collection.update_one({'UserID': account},
                                      {'$set': {'HasPhoto': True}},
                                      upsert=False)
    sources_collection.update_one({'UserID': account},
                                  {'$set': {'Username:': username, 'ChannelTitle': title, 'ChannelAbout': about,
                                            'Followers: ': followers_count, 'Location': location,
                                            'Date': registration_date}})


# Saving tweet data from fetcher to db
# Receive all tweet's data, such as user id, tweet id, date of tweet, text message, location, and so on.
def save_tweets_to_mongo(list_of_tweets, flag_tweet, user_id):
    now = datetime.now()
    sources_collection.update_one({'UserID': user_id},
                                  {'$set': {'OffsetId': flag_tweet, "LastParsed": now}}, upsert=False)
    for tweet in list_of_tweets:
        user_id = tweet['user_id']
        tweet_id = tweet['tweet_id']
        date_tweet = tweet['tweet_date']
        text_tweet = tweet['tweet_text']
        tweet_location = tweet['location']
        retweet_count = tweet['retweet_count']
        likes_count = tweet['likes_count']
        has_media = tweet['has_media']
        media = tweet['media']
        category = tweet['category']
        is_quote = tweet['is_quote']
        quote_id = tweet['quote_id']
        tweet = {'UserID': user_id, 'TweetID': tweet_id, 'Date': date_tweet, 'Text': text_tweet,
                 'Retweet': retweet_count, 'Likes': likes_count, 'Location': tweet_location,
                 'SourceType': "twitter", 'Category': category, 'HasMedia': has_media,
                 'Media': media, 'IsQuote': is_quote, 'QuoteID': quote_id}
        tweets_collection.insert_one(tweet)
        logging_info = f"Tweet id - {tweet_id} saved to raw data."
        logging.info(logging_info)


# Getting id of our last parsed tweet from db
# Receive user id, return tweet id(int)
def get_last_publ_from_mongodb(account):
    user_docs = sources_collection.find_one({'HasPhoto': True, 'UserID': account}, {'OffsetId': 1, '_id': 0})
    try:
        result = user_docs['OffsetId']
    except Exception as e:
        logging_info = f"There are no tweets in our DB, offset ID is empty. " \
                       f"Starting to get ALL data for account:{account}"
        logging.info(logging_info)
        logging.info(e)
        result = None
    return result
