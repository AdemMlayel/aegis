from pymongo import MongoClient
import logging
class SOURCE_NAME_PLACEHOLDER:
    def __init__(self,conn_params={},test_db=""):
        HOSTNAME_PLACEHOLDER = MongoClient(
            f"mongodb://{conn_params['username']}:{conn_params['password']}@{conn_params['host']}:{conn_params['port']}/{conn_params['authdb']}")
        HOSTNAME_PLACEHOLDER = test_db
    def get_document(self,collection_name,filter):
        HOSTNAME_PLACEHOLDER(f"{collection_name} {filter}")
        HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER)
        HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER)
        doc = HOSTNAME_PLACEHOLDER[HOSTNAME_PLACEHOLDER][collection_name].find_one(filter)
        doc['_id']=str(doc['_id'])
        HOSTNAME_PLACEHOLDER(doc)
        return doc
