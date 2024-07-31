import os
import tiktoken
from dotenv import load_dotenv
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.indices.prompt_helper import PromptHelper
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Document
from llama_index.llms.openai import OpenAI
from llama_index.core.settings import Settings  # Import the singleton instance

# Load environment variables from the .env file
load_dotenv()

# Retrieve the OpenAI API key from environment variables
api_key = os.getenv('OPENAI_API_KEY')

# Initialize the language model with the API key
llm = OpenAI(model='gpt-3.5-turbo', temperature=0, max_tokens=256, api_key=api_key)

# Initialize the embedding model
embed_model = OpenAIEmbedding(api_key=api_key)

# Initialize the tokenizer
tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo").encode

# Initialize the sentence splitter
sentence_splitter = SentenceSplitter(
    separator=" ",
    chunk_size=1024,
    chunk_overlap=20,
    tokenizer=tokenizer
)

# Initialize the prompt helper
prompt_helper = PromptHelper(
    context_window=4096,
    num_output=256,
    chunk_overlap_ratio=0.1,
    chunk_size_limit=None
)

# Configure the singleton settings instance
Settings._llm = llm
Settings._embed_model = embed_model
Settings._tokenizer = tokenizer
Settings._node_parser = sentence_splitter
Settings._prompt_helper = prompt_helper

# Load documents from data directory
directory_documents = SimpleDirectoryReader(input_dir='data').load_data()

# Print the total number of documents
print(f'Total number of documents: {len(directory_documents)}')

# Create the index
index = VectorStoreIndex.from_documents(
    directory_documents,
    service_context=Settings  
)

# load index
index.storage_context.persist(persist_dir="index_storage")

# Create a query engine
query_engine = index.as_query_engine(service_context=Settings)  

def query_index(query):
    response = query_engine.query(query)
    # Extract metadata
    sources = [node.node.metadata for node in response.source_nodes]
    return {"response": str(response), "sources": sources}
