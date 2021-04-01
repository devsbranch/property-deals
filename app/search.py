from flask import current_app


def add_to_index(index, model):
    """
    Adds property data into Elasticsearch.
    """
    if not current_app.elasticsearch:
        return
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    current_app.elasticsearch.index(index=index, id=model.id, body=payload)


def remove_from_index(index, model):
    """
    Deletes property data from Elasticsearch index.
    """
    if not current_app.elasticsearch:
        return
    current_app.elasticsearch.delete(index=index, id=model.id)


def query_index(index, query, page, per_page):
    """
    This function returns the list of search result IDs, and the total number of search results
    """
    if not current_app.elasticsearch:
        return [], 0  # Returns empty list if elastic search is not configured
    search = current_app.elasticsearch.search(
        index=index,
        body={
            "query": {
                "dis_max": {
                    "queries": [
                        {"match_phrase_prefix": {"name": query}},
                        {"match_phrase_prefix": {"desc": query}},
                        {"match_phrase_prefix": {"location": query}}
                    ]
                }
            },
            "from": (page - 1) * per_page, "size": per_page
        }
    )
    ids = [int(hit["_id"]) for hit in search["hits"]["hits"]]
    return ids, search["hits"]["total"]  # Return a list of property ids which to be used in a db query
