import asyncio
import json

import time
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

import parser


STARTUP_DELAY = 5
CONSUME_POLL_INTERVAL_SEC = 1
READ_TIMEOUT_SEC = 1


async def consumer():
    consumer = AIOKafkaConsumer('topic', bootstrap_servers='kafka:9092')  # , auto_offset_reset='earliest')
    producer = AIOKafkaProducer(bootstrap_servers='kafka:9092')

    await consumer.start()
    await producer.start()

    try:
        while True:
            # async for task in consumer:
            data = await consumer.getmany(timeout_ms=READ_TIMEOUT_SEC*1000)
            for tp, messages in data.items():
                for message in messages:
                    print(message)
                    task = json.loads(message.value.decode())

                    async for msg in parser.get_messages(parser.client, task['url'], task['last_message_id']):
                        await producer.send_and_wait("topic_result", json.dumps(msg).encode())
                        print(f'Replied with msg={msg}')

            print('Sleeping till the next attempt...')
            await asyncio.sleep(CONSUME_POLL_INTERVAL_SEC)

    except Exception as ex:
        print('EXCEPTION:', ex)

    finally:
        await consumer.stop()
        await producer.stop()


def main():
    print(f'CONSUMER: wait until broker is up and running {STARTUP_DELAY}...')
    time.sleep(STARTUP_DELAY)
    print('CONSUMER: start reading messages!')

    with parser.client:
        parser.client.loop.run_until_complete(consumer())


if __name__ == '__main__':
    main()