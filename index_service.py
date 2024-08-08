import os
import tiktoken
from dotenv import load_dotenv
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.indices.prompt_helper import PromptHelper
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Document
from llama_index.llms.openai import OpenAI
from llama_index.core.settings import Settings  # Import the singleton instance
from llama_index.core import PromptTemplate

# Load environment variables from the .env file
load_dotenv()

# Retrieve the OpenAI API key from environment variables
api_key = os.getenv('OPENAI_API_KEY')

# Initialize the language model with the API key
llm = OpenAI(model='gpt-4o-mini', temperature=0, max_tokens=256, api_key=api_key)

# Initialize the embedding model
embed_model = OpenAIEmbedding(api_key=api_key)

# Initialize the tokenizer
tokenizer = tiktoken.encoding_for_model("gpt-4o-mini").encode

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

# Custom SimpleDirectoryReader to include metadata
class CustomSimpleDirectoryReader(SimpleDirectoryReader):
    def load_data(self):
        documents = super().load_data()
        for document in documents:
            # Extract metadata from the content
            lines = document.text.split('\n')
            metadata = {}
            for line in lines[:3]:  # Assuming the first few lines contain metadata
                if line.startswith('Archive:'):
                    metadata['archive'] = line.replace('Archive:', '').strip()
                elif line.startswith('Filepath:'):
                    metadata['filepath'] = line.replace('Filepath:', '').strip()
            document.metadata = metadata
            # Debug prints to verify metadata
            # print(f"Document Metadata: {metadata}")
        return documents

# Load documents from data directory
directory_documents = CustomSimpleDirectoryReader(input_dir='data').load_data()

# Print the total number of documents
print(f'Total number of documents: {len(directory_documents)}')

# Create the index
index = VectorStoreIndex.from_documents(
    directory_documents,
    service_context=Settings  
)

# Load index
index.storage_context.persist(persist_dir="index_storage")

# Create a query engine
query_engine = index.as_query_engine(service_context=Settings)  

# Define the context
context = "Please generate responses using the provided course notes, with minimal additional input. Focus primarily on the documents for accuracy. Rephrase only when absolutely necessary."


# Create a prompt template
template = (
    "We have provided context information below. \n"
    "---------------------\n"
    "{context_str}"
    "\n---------------------\n"
    "Given this information, please answer the question: {query_str}\n"
)
qa_template = PromptTemplate(template)

def query_index(query):
    # Format the prompt using the custom template
    formatted_prompt = qa_template.format(context_str=context, query_str=query)
    
    # Use the formatted prompt to query the index
    response = query_engine.query(formatted_prompt)
    
    # Extract metadata
    sources = [{"archive": node.node.metadata.get('archive'), "filepath": node.node.metadata.get('filepath')} for node in response.source_nodes]
    
    return {"response": str(response), "sources": sources}
