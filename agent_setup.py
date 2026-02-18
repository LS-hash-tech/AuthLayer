from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

path1 = r"/Users/laynesingh/AuthLayer/knowledge_base/general_authentication.md"
path2 = r"/Users/laynesingh/AuthLayer/knowledge_base/margiela_authentication.md"

file1 = open (path1)
file2 = open (path2)

print(file1.read())
print(file2.read())

text1 = file1.read()
text2 = file2.read()

doc1 = Document(page_content=text1, metadata={"source": "general_authentication.md"})
doc2 = Document(page_content=text2, metadata={"source": "margiela_authentication.md"})

''' [1, 3] '''

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
texts = text_splitter.split_documents([doc1, doc2])
