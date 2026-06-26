from elasticsearch import AsyncElasticsearch
from app.config import settings

es_client: AsyncElasticsearch = None
DOCTORS_INDEX = "helia_doctors"


async def init_elasticsearch():
    global es_client
    kwargs = {"hosts": [settings.elasticsearch_url]}
    if settings.elastic_password:
        kwargs["basic_auth"] = (settings.elastic_username, settings.elastic_password)

    es_client = AsyncElasticsearch(**kwargs)

    # Create doctors index with mapping if it doesn't exist
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
