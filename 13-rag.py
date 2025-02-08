#!/usr/bin/env python3

# Import necessary modules
from langchain_openai import ChatOpenAI
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_core.vectorstores import InMemoryVectorStore
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize embedding model
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

# Create vector store from texts
vectorstore = InMemoryVectorStore.from_texts(
    [f"{animal} eats {food}" for animal, food in animals_and_foods],
    embedding=embedding_model,
)

# Use the vectorstore as a retriever
retriever = vectorstore.as_retriever()

# Initialize LLM model
# llm = OllamaLLM(model="llama2")
llm = ChatOpenAI(model="gpt-4")

# Create prompt template

prompt = PromptTemplate.from_template("""
* You are a helpful assistant.
* Your goal is never to answer the question I define but to rephrase it to one word only - a specific animal name, not a class of animals.
* Never say what the animal eats, just the animal name.
* Answer with a single word only (I will be fired for you answering more words)
* QUESTION:"{question}"
""") # This is a prompt for vector db that should translate a user's prompt to something answerable by a vector db that maps animals and their food


# Create LLM chain
chain = {"question": RunnablePassthrough()} | prompt | llm

# Main function for chat interface
def main():
    print("Welcome to the Local LLM Chat Interface! (Type 'quit' to exit)")
    while True:
        user_input = input("\n1. Your question: ")
        
        if user_input.lower() == 'quit':
            print("Goodbye!")
            break


# Retrieve the most similar text
        print("Chain prompt:", prompt.template)

        question_for_vector_db = chain.invoke(user_input).content + " eats what?" 
        print("2. Question for vector db:", question_for_vector_db)
        retrieved_documents  = retriever.invoke(question_for_vector_db, num_results=5)

        # Show the retrieved document's content
        print("3. Retrieved documents:")
        for document in retrieved_documents:
            print(document.page_content)

        context = "\n* ".join([doc.page_content for doc in retrieved_documents])
        q = "This is the absolute truth:\n" + context + "\n\nNow answer the following question:\n" + user_input
        print("4. Question to LLM after we enrich it with the context:", q)
        response = chain.invoke(q)
        print("5.Answer:", response.content)

# Run main function
if __name__ == "__main__":
    main()
