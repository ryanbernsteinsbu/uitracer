import os
import nest_asyncio
import pandas as pd
from dotenv import find_dotenv, load_dotenv 
from langsmith import Client
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langsmith import traceable
from langsmith import evaluate
# from langsmith.evaluation import LangChainStringEvaluator

load_dotenv(find_dotenv())
os.environ["LANGCHAIN_API_KEY"] = str(os.getenv("LANGCHAIN_API_KEY"))
os.environ["GOOGLE_API_KEY"] = str(os.getenv("MODEL_API_KEY"))
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_PROJECT"] = "ui-dataset-langsmith"

client = Client()

llm = ChatGoogleGenerativeAI(model="gemini-3.8-flash")
# print(llm.invoke("What can you do?"))

inputs = [] # we will populate this with some form of ui rep + task + metadata

dataset_name = "UI Navigation Dataset"

dataset = client.create_dataset(
    dataset_name=dataset_name,
    description="UIs and their navigation",
)

for input_prompt in inputs:
    client.create_example(
        inputs={"question": input_prompt},
        outputs=None,
        dataset_id=dataset.id,
    )


