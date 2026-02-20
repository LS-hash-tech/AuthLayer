# agent_setup.py - loads knowledge base, chunks it, embeds it, stores it
# this is the RAG backbone of the whole thing

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
import os
from dotenv import load_dotenv

load_dotenv()


def setup_knowledge_base():
    # reading the md files - these are the authentication guides i wrote
    path1 = "knowledge_base/general_authentication.md"
    path2 = "knowledge_base/margiela_authentication.md"

    file1 = open(path1)
    file2 = open(path2)

    text1 = file1.read()
    text2 = file2.read()

    file1.close()
    file2.close()

    # wrapping into langchain documents so we can chunk them
    doc1 = Document(
        page_content=text1, metadata={"source": "general_authentication.md"}
    )
    doc2 = Document(
        page_content=text2, metadata={"source": "margiela_authentication.md"}
    )

    # splitting into chunks - 1000 chars each with 200 overlap so we dont lose context at edges
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents([doc1, doc2])

    print(f"loaded {len(texts)} chunks from knowledge base")

    # embeddings + vectorstore
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    vectorstore = InMemoryVectorStore.from_documents(
        texts,
        embedding=embeddings,
    )

    return vectorstore


# quick test if u run this file directly
if __name__ == "__main__":
    vs = setup_knowledge_base()
    results = vs.similarity_search("how to authenticate margiela GATs")
    print(results[0].page_content)
