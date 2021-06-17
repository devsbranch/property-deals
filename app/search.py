import os
from decouple import config
from flask import current_app
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Document, Keyword, Text, Search, Integer
from elasticsearch_dsl.connections import connections

es_http_auth_username = os.environ.get("ELASTICSEARCH_USERNAME", config("ELASTICSEARCH_USERNAME"))
es_http_auth_password = os.environ.get("ELASTICSEARCH_PASS", config("ELASTICSEARCH_PASS"))


# Create global connection to ElasticSearch
connections.create_connection(hosts=[os.environ.get("ELASTICSEARCH_URL", "localhost")],
                              http_auth=(es_http_auth_username, es_http_auth_password))


es = Elasticsearch([os.environ.get("ELASTICSEARCH_URL", config("ELASTICSEARCH_URL"))],
                   http_auth=(es_http_auth_username, es_http_auth_password))

s = Search(using=es, index="property_index")


class PropertyDataMapping(Document):
    """
    This class create a mapping for the data that will be indexed into ElasticSearch from the database.
    """

    id = Integer()
    name = Text(analyzer="standard", fields={"raw": Keyword()})
    desc = Text(analyzer="standard")
    location = Text(analyzer="standard")

    class Index:
        name = "property_index"  # Name of the index where the data that will be searched will be indexed
        settings = {"number_of_shards": 1}

    def save(self, **kwargs):
        return super(PropertyDataMapping, self).save(**kwargs)


def search_docs(search_term, page, per_page):
    """
    Searches for documents in ElasticSearch index with the search term provided. The results returned are ids
    of the property listings matching the search term.
    """
    body = {
        "query": {
            "multi_match": {
                "query": search_term,
                "fields": ["name^3", "desc^1", "location"],
                "fuzziness": 1,
            }
        },
        "from": (page - 1) * per_page,
        "size": per_page,
    }

    # Here I use ElasticSearch client instead of ElasticSearch_dsl SDK so that the pagination
    # can be included in the query
    response = es.search(index="property_index", body=body)
    ids = [int(hit["_id"]) for hit in response["hits"]["hits"]]
    total_results = response["hits"]["total"]["value"]
    return ids, total_results


def add_to_index(id, name, desc, location):
    """
    Saves the data of the fields "id", "name", "desc" and "location into ElasticSearch index.
    """
    data_to_index = PropertyDataMapping(
        meta={"id": id}, id=id, name=name, desc=desc, location=location
    )
    data_to_index.save()


def index_existing_data(db_model):
    """
    This function can be used to indexed existing data from the database into ElasticSearch.
    """
    for obj in db_model.query.all():
        add_to_index(obj.id, obj.name, obj.desc, obj.location)


def delete_from_index(id):
    """
    Saves the data from ElasticSearch index by id.
    """
    doc_to_delete = PropertyDataMapping.get(id=id)
    doc_to_delete.delete()
