#!/usr/bin/env python3
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize the LLM
llm = ChatOpenAI(model="gpt-4")

# Create a simple prompt template
prompt = PromptTemplate(
    input_variables=["question"],
    template="Please answer the following question: {question}"
)

# Create the chain
chain = {"question": RunnablePassthrough()} | prompt | llm
def main():
    print("Welcome to the GPT-4 Chat Interface! (Type 'quit' to exit)")
    while True:
        user_input = input("\nYour question: ")
        
        if user_input.lower() == 'quit':
            print("Goodbye!")
            break
            
        print("\nResponse: ")
        # Remove callbacks from here since they're now in the LLM
        for chunk in chain.stream(user_input):
            print(chunk.content, end="", flush=True)
        print()  # Add newline after response

if __name__ == "__main__":
    main()
