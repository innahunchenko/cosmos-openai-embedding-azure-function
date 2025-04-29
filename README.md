# cosmos-openai-embedding-azure-function
Python Azure Function that runs every 24 hours to generate text embeddings from Cosmos DB documents using Azure OpenAI. All services are accessed securely via User-Assigned Managed Identity (UAMI) without API keys.

This Azure Function is packaged as a `.zip` archive. To deploy it to Azure, follow these steps:

1. Ensure that you have the **Azure CLI** installed and authenticated.
2. Deploy the function using the following command:

   ```bash
   az functionapp deployment source config-zip \
     --resource-group backend \
     --name cosmos-openai-embedding-azure-function \
     --src cosmos-openai-embedding-azure-function.zip
