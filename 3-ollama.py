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

prompt = PromptTemplate(
    input_variables=["question"],
    template="Please answer the following question: {question}"
)

chain = LLMChain(llm=llm, prompt=prompt)

def main():
    print("Welcome to the Local LLM Chat Interface! (Type 'quit' to exit)")
    while True:
        user_input = input("\nYour question: ")
        
        if user_input.lower() == 'quit':
            print("Goodbye!")
            break
            
        try:
            response = chain.invoke({"question": user_input})
            print("\nResponse:", response["text"])
        except Exception as e:
            print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
