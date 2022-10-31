from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from typing import List
from dataclasses import dataclass
import logging

HEADERS = {'content-type': 'application/json'}
INDEX_NAME = 'messages'
DOC_TYPE='message'
from server import app
_logger = logging.getLogger(__name__)

@dataclass
class SearchResult():
    """Represents a message returned from elasticsearch."""
    id: str
    channel: str
    channel_name: str
    message: str
    image: str
    score: float
    date: str

    def from_doc(doc) -> 'SearchResult':
        return SearchResult(
                id = doc.meta.id,
                channel_name = doc.channel.replace('https://t.me/', ''),
                channel = doc.channel,
                message = doc.message[:256] + ('...' if len(doc.message) > 256 else ''),
                image = doc.image,
                score = doc.meta.score,
                date = doc.date,
            )

    def from_dict(doc) -> 'SearchResult':
        return SearchResult(
                id = doc.get('id'),
                channel_name = doc.get('channel_name'),
            )

@dataclass
class Message():
    """Represents a message returned from elasticsearch."""
    id: str
    channel_name: str


def search(term: str, exact_term: bool) -> List[SearchResult]:
    client = Elasticsearch(["elasticsearch:9200"])

    # Elasticsearch 6 requires the content-type header to be set, and this is
    # not included by default in the current version of elasticsearch-py
    client.transport.connection_pool.connection.headers.update(HEADERS)

    s = Search(using=client, index=INDEX_NAME, doc_type=DOC_TYPE)

    if exact_term:
        name_query = {
            'term':{
                'message': term.lower()
            }
        }
    else:
        name_query = {
                'match':{
                    'message.russian_analyzed':{
                        "query": term,
                        "fuzziness": "AUTO",
                        "operator": "and"
                    }
                }
        }

    result = s.query(name_query)
    app.logger.info(f'Query: {result.to_dict()}')

    docs = result.execute()

    return [SearchResult.from_doc(d) for d in docs], docs.hits.total['value']