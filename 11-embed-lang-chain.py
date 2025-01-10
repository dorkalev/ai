#!/usr/bin/env python3

# ollama pull mxbai-embed-large
# ollama pull ll
# or all-minilm	

from langchain_ollama import OllamaEmbeddings

embedding_model = OllamaEmbeddings(model="llama3")
response = embedding_model.embed_query("Cow")

print(response)