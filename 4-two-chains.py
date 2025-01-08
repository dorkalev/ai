#!/usr/bin/env python3

# brew install ollama
# ollama serve
# ollama run llama2 "Hello, how are you?"

from langchain_ollama import OllamaLLM
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

llm = OllamaLLM(model="llama2")

# First chain: Rephrase the question with rhyming
rhyming_prompt = PromptTemplate(
    input_variables=["question"],
    template="Please rephrase the following question with rhyming: {question}"
)
rhyming_chain = {"question": RunnablePassthrough()} | rhyming_prompt | llm

# Second chain: List websites with additional information
info_prompt = PromptTemplate(
    input_variables=["question"],
    template="List websites with additional information about: {question}"
)
info_chain = { "question": RunnablePassthrough() } | info_prompt | llm


def main():
    print("Welcome to the Local LLM Chat Interface! (Type 'quit' to exit)")
    while True:
        user_input = input("\nYour question: ")
        
        if user_input.lower() == 'quit':
            print("Goodbye!")
            break
            
        # First chain: Rephrase with rhyming
        rhymed_response = rhyming_chain.invoke(user_input)
        print("\nRhymed Question:", rhymed_response)
        
        # Second chain: List websites
        info_response = info_chain.invoke(rhymed_response)
        print("\nWebsites with additional info:", info_response)

if __name__ == "__main__":
    main()
