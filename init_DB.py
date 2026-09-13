from qdrant_client import QdrantClient
from qdrant_client.models import Filter

client = QdrantClient(
    url= "https://9b6ff33b-df7c-4328-b2f3-fe5d55ea8955.us-east-2-0.aws.cloud.qdrant.io",
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6NGQ5MTg0OTAtNzVmNi00NmU3LTlkZDMtYzVjZWExNDc4YzE3In0.nkB3ORVFkVFCJlSID8vbn1JY631GEjZVC9yrd_i548I",
)

COLLECTION_NAME = "hr_documents"

client.delete(
    collection_name=COLLECTION_NAME,
    points_selector=Filter(),
)

print("Qdrant data reset successfully.")