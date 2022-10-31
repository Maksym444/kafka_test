from flask import Flask, render_template, request

from .server import app
from .search import search, SearchResult, Message

import logging

_logger = logging.getLogger(__name__)

@app.route('/')
@app.route('/index')
def index():
    """
    Search for products across a variety of terms, and show 9 results for each.
    """
    query = ''
    num_results = 50
    messages = search(query, num_results, num_results)
    return render_template(
        'index.html',
        message=messages,
        search_term=query,
    )


@app.route('/search', methods=['GET'])
def search_messages():
    """
    Execute a search for a specific search term.

    Return the top 50 results.
    """
    app.logger.info('Searching for messages')

    query = request.args.get('q')
    exact_term = bool(request.args.get('exact_term'))
    num_results = 50
    messages, hits_total = search(query, exact_term, num_results)

    app.logger.info(f'Found {len(messages)} messages')
    app.logger.info(f'exact_term: {exact_term}')
    # app.logger.info(f'Messages={messages[0]}')

    return render_template(
        'index.html',
        messages=messages,
        query=query,
        exact_term=exact_term,
        hits_total=hits_total,
    )


@app.route('/messages/<string:channel_name>/<int:message_id>', methods=['GET'])
def single_message(channel_name, message_id):
    """
    """
    message = Message(
        id=message_id,
        channel_name=channel_name,
    )

    return render_template(
        'message.html',
        message=message
    )