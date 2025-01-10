#!/usr/bin/env python3

from langchain_ollama import OllamaEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore

embedding_model = OllamaEmbeddings(model="llama3")

# List of animals and what they eat
animals_and_foods = [
    ("Cow", "Grass"),
    ("Lion", "Meat"),
    ("Rabbit", "Carrots"),
    ("Panda", "Bamboo"),
    ("Kangaroo", "Grass"),
    ("Elephant", "Fruits"),
    ("Giraffe", "Leaves"),
    ("Tiger", "Meat"),
    ("Koala", "Eucalyptus leaves"),
    ("Horse", "Hay"),
    ("Sheep", "Grass"),
    ("Goat", "Grass"),
    ("Chicken", "Grains"),
    ("Duck", "Insects"),
    ("Pig", "Vegetables"),
    ("Dog", "Dog food"),
    ("Cat", "Cat food"),
    ("Bear", "Fish"),
    ("Deer", "Grass"),
    ("Monkey", "Fruits")
]

vectorstore = InMemoryVectorStore.from_texts(
    [f"{animal} eats {food}" for animal, food in animals_and_foods],
    embedding=embedding_model,
)

# Use the vectorstore as a retriever
retriever = vectorstore.as_retriever()

# # Retrieve the most similar text
retrieved_documents = retriever.invoke("who eats hay?")

# # show the retrieved document's content
for document in retrieved_documents:
    print(document.page_content)

