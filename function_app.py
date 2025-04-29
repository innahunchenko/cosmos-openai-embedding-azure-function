import azure.functions as func
import datetime
import json
import logging
import os
from azure.cosmos import CosmosClient
from azure.identity import ManagedIdentityCredential

app = func.FunctionApp()

COSMOS_DB_URL = os.getenv("COSMOSDB_URL") #"https://datapilotdb.documents.azure.com:443/"
DATABASE_NAME = os.getenv("COSMOS_DB_DATABASE", "DataPilot")
CONTAINER_NAME = os.getenv("COSMOS_DB_CONTAINER", "Charts")
LAST_HOURS = int(os.getenv("LAST_HOURS", 24))

def get_recent_documents():
    """Retrieves documents from Cosmos DB that were updated in the last 24 hours."""
    
    credential = ManagedIdentityCredential()
    timestamp_last_hours_ago = int((datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=LAST_HOURS)).timestamp())

    client = CosmosClient(COSMOS_DB_URL, credential)
    database = client.get_database_client(DATABASE_NAME)
    container = database.get_container_client(CONTAINER_NAME)
    query = "SELECT * FROM c WHERE c._ts >= @timestamp"
    parameters = [{"name": "@timestamp", "value": timestamp_last_hours_ago}]
    documents = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
    
    logging.info(f"Found {len(documents)} documents.")

    for doc in documents:
         logging.info(json.dumps(doc, indent=4))

    return documents

@app.timer_trigger(schedule="0 * * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False)
def timer_trigger(myTimer: func.TimerRequest) -> None:
    
    if myTimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Python timer trigger function executed.')

    try:
        get_recent_documents()
        
        logging.info("Processing completed successfully.")
    except Exception as e:
        logging.error(f"Function execution failed: {e}")

