#!/usr/bin/env python3

# brew install ollama
# ollama serve
# ollama run llama2 "Hello, how are you?"

from langchain_ollama import OllamaLLM
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

llm = OllamaLLM(model="llama2")

# First chain: Rephrase the question with rhyming
rhyming_prompt = PromptTemplate(
    input_variables=["question"],
    template="Please rephrase the following question with rhyming: {question}"
)
rhyming_chain = LLMChain(llm=llm, prompt=rhyming_prompt)

# Second chain: List websites with additional information
info_prompt = PromptTemplate(
    input_variables=["question"],
    template="List websites with additional information about: {question}"
)
info_chain = LLMChain(llm=llm, prompt=info_prompt)

def main():
    print("Welcome to the Local LLM Chat Interface! (Type 'quit' to exit)")
    while True:
        user_input = input("\nYour question: ")
        
        if user_input.lower() == 'quit':
            print("Goodbye!")
            break
            
        try:
            # First chain: Rephrase with rhyming
            rhymed_response = rhyming_chain.invoke({"question": user_input})
            print("\nRhymed Question:", rhymed_response["text"])
            
            # Second chain: List websites
            info_response = info_chain.invoke({"question": user_input})
            print("\nWebsites with additional info:", info_response["text"])
        except Exception as e:
            print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
