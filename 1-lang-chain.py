#!/usr/bin/env python3
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(model="gpt-4")

prompt = PromptTemplate(
    input_variables=["question"],
    template="Please answer the following question: {question}"
)

chain = prompt | llm

def main():
    print("Welcome to the GPT-4 Chat Interface! (Type 'quit' to exit)")
    while True:
        user_input = input("\nYour question: ")
        
        if user_input.lower() == 'quit':
            print("Goodbye!")
            break
            
        response = chain.invoke({"question": user_input})
        print("\nResponse:", response.content)

if __name__ == "__main__":
    main()
