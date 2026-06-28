import boto3
from HOSTNAME_PLACEHOLDER import keyword
import logging
class SOURCE_NAME_PLACEHOLDER:
    def __init__(self):
        # Initialize the DynamoDB resource and table attributes
        HOSTNAME_PLACEHOLDER = None
        HOSTNAME_PLACEHOLDER = None

    @keyword
    def get_dynamo_resource(self):
        """Returns a boto3 DynamoDB resource."""
        if HOSTNAME_PLACEHOLDER is None:
            HOSTNAME_PLACEHOLDER = HOSTNAME_PLACEHOLDER('dynamodb', region_name='eu-central-1')  # Change region if necessary
        return HOSTNAME_PLACEHOLDER

    @keyword
    def get_dynamo_table(self, dynamo_resource, table_name):
        """Returns a DynamoDB table instance."""
        if HOSTNAME_PLACEHOLDER is None:
            HOSTNAME_PLACEHOLDER = dynamo_resource.Table(table_name)
        return HOSTNAME_PLACEHOLDER

    @keyword
    def insert_record_into_table(self, table, item):
        """Inserts a record into the DynamoDB table."""
        try:
            put_response = table.put_item(Item=item)
            HOSTNAME_PLACEHOLDER(f"DynamoDB storing response: {put_response}")
        except Exception as e:
            raise Exception(f"Error storing on DynamoDB: {str(e)}")
    