import azure.functions as func
import datetime
import json
import logging
import os
import openapi
import requests
from azure.cosmos import CosmosClient
from azure.identity import ManagedIdentityCredential

app = func.FunctionApp()

COSMOS_DB_URL = os.getenv("COSMOSDB_URI")
UAMI_CLIENT_ID = os.getenv("UAMI_CLIENT_ID")
DATABASE_NAME = os.getenv("COSMOS_DB_DATABASE", "DataPilot")
CONTAINER_NAME = os.getenv("COSMOS_DB_CONTAINER", "Charts")
LAST_HOURS = int(os.getenv("LAST_HOURS", 24))
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")

def get_embeddings_from_openai(text: str) -> list:
    """Calls Azure OpenAI API to generate embeddings for the given text."""
    if not text:
        return []

    credential = ManagedIdentityCredential(client_id=UAMI_CLIENT_ID)
    token = credential.get_token("https://cognitiveservices.azure.com/.default").token

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {"input": text}

    response = requests.post(AZURE_OPENAI_ENDPOINT, headers=headers, json=payload)
    response.raise_for_status()  

    embedding = response.json()["data"][0]["embedding"]

    return embedding

@app.timer_trigger(schedule="0 * * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False)
def timer_trigger(myTimer: func.TimerRequest) -> None:
    
    if myTimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Python timer trigger function executed.')

    try:
        credential = ManagedIdentityCredential(client_id=UAMI_CLIENT_ID)
        timestamp_last_hours_ago = int((datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=LAST_HOURS)).timestamp())

        client = CosmosClient(COSMOS_DB_URL, credential)
        database = client.get_database_client(DATABASE_NAME)
        container = database.get_container_client(CONTAINER_NAME)
        query = "SELECT * FROM c WHERE c._ts >= @timestamp"
        parameters = [{"name": "@timestamp", "value": timestamp_last_hours_ago}]
        documents = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))

        for document in documents:
            chart_title = document.get("chart_title", "")
            chart_description = document.get("chart_description", "")

            document["chart_title_vector"] = get_embeddings_from_openai(chart_title)
            document["chart_description_vector"] = get_embeddings_from_openai(chart_description)

            container.upsert_item(document)
        
        logging.info("Processing completed successfully.")
    except Exception as e:
        logging.error(f"Function execution failed: {e}")

