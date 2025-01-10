#!/usr/bin/env python3

# ollama pull mxbai-embed-large
# or all-minilm	

import ollama

response = ollama.embeddings(model="mxbai-embed-large", prompt="Cow")

print(response)