#!/usr/bin/env python3

# brew install ollama
# ollama serve
# ollama run llama2 "Hello, how are you?"

from langchain_ollama import OllamaLLM
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

llm = OllamaLLM(model="llama2")

# First chain: Rephrase the question with rhyming
rhyming_prompt = ChatPromptTemplate.from_template("""
List websites with additional information about: {question}
""")

rhyming_chain = {"question": RunnablePassthrough() } | rhyming_prompt | llm 

# Second chain: List websites with additional information
info_prompt = ChatPromptTemplate.from_template("""
Just give the URL for each of them: {question}
""")

info_chain = {"question": RunnablePassthrough() } | info_prompt | llm 

# Define the chains using | operator
composed_chain = (
    {"question": RunnablePassthrough() } | 
    rhyming_chain | 
    info_chain
)

def main():
    print("Welcome to the Local LLM Chat Interface! (Type 'quit' to exit)")
    while True:
        user_input = input("\nYour question: ")
        
        if user_input.lower() == 'quit':
            print("Goodbye!")
            break
            
        # try:
            # Run both chains in sequence using the pipe operator
        responses = composed_chain.invoke(user_input)
        print("\nWebsites with additional info:", responses)
        # except Exception as e:
        #     print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
