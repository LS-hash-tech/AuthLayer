from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import getpass
import os
from langchain_openai import OpenAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from dotenv import load_dotenv

load_dotenv()

path1 = r"/Users/laynesingh/AuthLayer/knowledge_base/general_authentication.md"
path2 = r"/Users/laynesingh/AuthLayer/knowledge_base/margiela_authentication.md"

# opening, reading and printing(to test) from .md files

file1 = open (path1)
file2 = open (path2)

text1 = file1.read()
text2 = file2.read()

# print(text1) # keep these out if you want your terminal to be cleaner
# print(text2) # keep these out if you want your terminal to be cleaner

doc1 = Document(page_content=text1, metadata={"source": "general_authentication.md"})
doc2 = Document(page_content=text2, metadata={"source": "margiela_authentication.md"})

''' [1, 3] '''

# splitting text in chunks and returning the total of them

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
texts = text_splitter.split_documents([doc1, doc2])

print(len(texts))

# embeddings + vectorstore

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

vectorstore = InMemoryVectorStore.from_documents(
    texts,
    embedding=embeddings,
)

retriver = vectorstore.as_retriever()

retrived_documents = retriver.invoke("how to authenticate a pair of margiela GATs?")

print(retrived_documents[0].page_content)
