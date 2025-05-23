import os
import requests
from dotenv import load_dotenv
from llama_parse import LlamaParse
from llama_index.vector_stores.astra_db import AstraDBVectorStore
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

# Load environment variables
load_dotenv()

# Get all required API keys and parameters
llama_cloud_api_key = os.getenv("LLAMA_CLOUD_API_KEY")
api_endpoint = os.getenv("ASTRA_DB_API_ENDPOINT")
token = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
openai_api_key = os.getenv("OPENAI_API_KEY")

# Configure global Settings
Settings.llm = OpenAI(model="gpt-4", temperature=0.1)
Settings.embed_model = OpenAIEmbedding(
    model="text-embedding-3-small", embed_batch_size=100
)

# Download a PDF for indexing
url = "https://arxiv.org/pdf/1706.03762.pdf"
file_path = "./attention.pdf"
response = requests.get(url, timeout=30)
if response.status_code == 200:
    with open(file_path, "wb") as file:
        file.write(response.content)
    print("Download complete.")
else:
    print("Error downloading the file.")

# Load and parse the document
documents = LlamaParse(result_type="text").load_data(file_path)
print(documents[0].get_content()[10000:11000])

# Setup for storing in AstraDB
astra_db_store = AstraDBVectorStore(
    token=token,
    api_endpoint=api_endpoint,
    collection_name="astra_v_table_llamaparse",
    embedding_dimension=1536
)

# Parse nodes from documents and output a snippet for verification
node_parser = SimpleNodeParser()
nodes = node_parser.get_nodes_from_documents(documents)
print(nodes[0].get_content())

# Setup storage context
storage_context = StorageContext.from_defaults(vector_store=astra_db_store)

# Indexing and query engine setup
index = VectorStoreIndex(nodes=nodes, storage_context=storage_context)
query_engine = index.as_query_engine(similarity_top_k=15)

# Execute a query
query = "What is Multi-Head Attention also known as?"
response_1 = query_engine.query(query)
print("\n***********New LlamaParse+ Basic Query Engine***********")
print(response_1)

# Query for an example with expected lack of context
query = "What is the color of the sky?"
response_2 = query_engine.query(query)
print("\n***********New LlamaParse+ Basic Query Engine***********")
print(response_2)