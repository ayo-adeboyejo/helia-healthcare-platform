from elasticsearch import AsyncElasticsearch
from app.config import settings

es_client: AsyncElasticsearch = None
DOCTORS_INDEX = "helia_doctors"


async def init_elasticsearch():
    global es_client

    # Elasticsearch 8.x Python client defaults to HTTPS.
    # Our container runs xpack.security over plain HTTP — no TLS cert configured.
    # We pass the URL with explicit http:// scheme and disable SSL verification
    # to force plain HTTP connections.
    es_client = AsyncElasticsearch(
        hosts=[settings.elasticsearch_url],
        basic_auth=(settings.elastic_username, settings.elastic_password),
        verify_certs=False,
        ssl_show_warn=False,
    )

    # Verify connection before proceeding
    await es_client.info()

    # Create doctors index with mapping if it does not exist
    if not await es_client.indices.exists(index=DOCTORS_INDEX):
        await es_client.indices.create(
            index=DOCTORS_INDEX,
            mappings={
                "properties": {
                    "id":               {"type": "keyword"},
                    "first_name":       {"type": "text", "analyzer": "standard"},
                    "last_name":        {"type": "text", "analyzer": "standard"},
                    "specialty":        {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "qualification":    {"type": "text"},
                    "experience_years": {"type": "integer"},
                    "bio":              {"type": "text"},
                    "consultation_fee": {"type": "float"},
                    "languages":        {"type": "text"},
                    "clinic_address":   {"type": "text"},
                    "rating":           {"type": "float"},
                    "total_reviews":    {"type": "integer"},
                    "is_available":     {"type": "boolean"},
                    "is_approved":      {"type": "boolean"},
                }
            }
        )


async def close_elasticsearch():
    if es_client:
        await es_client.close()


async def get_es() -> AsyncElasticsearch:
    return es_client
