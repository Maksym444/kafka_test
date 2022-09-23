from telethon.errors import ChannelInvalidError
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.messages import GetFullChatRequest
from pathlib import Path
import traceback


async def get_full_channel_info_and_entity(client, channel):
    try:
        if isinstance(channel, str):
            ch = await client.get_entity(f'{channel}')
            ch_full = await client(GetFullChannelRequest(channel=ch))
            return ch_full.full_chat.about, ch
        elif isinstance(channel, int):
            ch = await client.get_entity(channel)
            if str(ch).startswith('Chat'):
                ch_full = await client(GetFullChatRequest(chat_id=ch.id))
                return ch_full, ch
            else:
                ch_full = await client(GetFullChannelRequest(channel=ch))
                return ch_full.full_chat.about, ch
    except TypeError:
        pass


async def get_photo(client, entity):
    photo = await client.get_profile_photos(entity)
    if len(photo) < 1:
        return None
    else:
        photo = await client.download_media(photo[0], f"{entity.id}.jpg")
        return photo


async def get_channel_info(client, channel):
    entity = await client.get_entity(channel)
    return entity


async def get_messages(client, channel_url, channel_id, last_message_id, limit):
    channel = await client.get_input_entity(channel_url)
    async for message in client.iter_messages(
        # entity=channel_url,
        entity=channel,
        reverse=True,
        offset_id=last_message_id,
        # min_id=last_message_id,
        limit=limit
    ):
        try:
            if message.replies and message.replies.replies > 0:
                replies = []
                async for reply_message in client.iter_messages(entity=channel, reply_to=message.id):
                    d = dict()
                    has_replies = True
                    d['user_id'] = reply_message.sender_id
                    d['message'] = reply_message.message
                    d['reply_date'] = str(reply_message.date)
                    d['post_author'] = message.post_author
                    if reply_message.sender_id is not None:
                        filename = f'media/users/{channel_id}/{reply_message.sender_id}.jpg'
                        profile_photo_file = Path(filename)
                        if not profile_photo_file.exists():
                            profile_photo_reply = await client.download_profile_photo(
                                entity=reply_message.sender_id,
                                file=filename
                            )
                        else:
                            profile_photo_reply = filename
                        d['user_avatar'] = profile_photo_reply
                    if reply_message.media is not None:
                        d['has_media'] = True
                        # d['media_list'] = await parse_media(reply_message, path_to_files, channel_id,
                        #                     working_client)
                    else:
                        d['has_media'] = False
                        d['media_list'] = []
                    replies.append(d)
            else:
                has_replies = False
                replies = []
        except AttributeError as e:
            # print(e)
            has_replies = False
            replies = []
        except ChannelInvalidError as e:
            print(f'EXCEPTION: {e}')
            print(traceback.format_exc())
            # raise

        # EACH MESSAGE
        new_message = dict()
        # new_message['channel_id'] = entity.id
        # new_message['channel_about'] = entity.title
        # new_message['channel_title'] = entity.title
        # new_message['category'] = category
        # new_message['from_id'] = message.from_id.user_id
        new_message['id'] = message.id
        new_message['message'] = message.message or ''
        # new_message['date'] = str(datetime.now()) #  add time
        new_message['date'] = str(message.date) #  add time
        new_message['date_raw'] = (message.date) #  add time
        new_message['channel_url'] = channel_url
        new_message['has_replies'] = has_replies
        new_message['replies'] = replies
        # new_message['source_type'] = 'telegram'
        # new_message['tags'] = source['Tags']
        try:
            profile_photo = await client.download_profile_photo(message.sender_id, f'media/{channel_id}/{message.sender_id}.jpg')
            new_message['user_avatar'] = profile_photo
        except Exception:
            pass
        if message.media is not None:
            if message.grouped_id is None:
                new_message['grouped'] = False
                new_message['grouped_id'] = 0
            else:
                new_message['grouped'] = True
                new_message['grouped_id'] = message.grouped_id
            new_message['has_media'] = True
            # new_message['media_list'] = await parse_media(message, path_to_files, channel_id,
            #                                               working_client)
        else:
            new_message['has_media'] = False
            new_message['media_list'] = []
        print(new_message)
        print('----------------------------')

        yield new_message

# if __name__ == '__main__':
#     with client:
#         client.loop.run_until_complete(get_messages(client, 'https://t.me/mudak', 0))
