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

rhyming_prompt = ChatPromptTemplate.from_template("""
Find 10 words that rhyme with: {question}
""")

chain  = {"question": RunnablePassthrough()} | rhyming_prompt | llm

def main():
    print("Welcome to the Local LLM Chat Interface! (Type 'quit' to exit)")
    while True:
        user_input = input("\nYour question: ")
        
        if user_input.lower() == 'quit':
            print("Goodbye!")
            break
            
        responses = chain.batch(user_input.split(','))
        for response in responses:
            print("\nResponse:", response)

if __name__ == "__main__":
    main()
