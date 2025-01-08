#!/usr/bin/env python3
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.callbacks.base import BaseCallbackHandler
from dotenv import load_dotenv
import os

# Add streaming callback handler
class StreamingHandler(BaseCallbackHandler):
    def __init__(self):
        self.current_token = ""

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.current_token += token
        # If we encounter a space or punctuation, print the accumulated word
        if token.endswith(' ') or token in '.,!?;:':
            print(self.current_token, end='', flush=True)
            self.current_token = ""
        
    def on_llm_end(self, *args, **kwargs) -> None:
        # Print any remaining token at the end
        if self.current_token:
            print(self.current_token, end='', flush=True)

# Load environment variables
load_dotenv()

# Initialize the LLM
llm = ChatOpenAI(
    model="gpt-4",
    temperature=0.7,
    streaming=True,
    callbacks=[StreamingHandler()]
)

# Create a simple prompt template
prompt = PromptTemplate(
    input_variables=["question"],
    template="Please answer the following question: {question}"
)

# Create the chain
chain = prompt | llm
def main():
    print("Welcome to the GPT-4 Chat Interface! (Type 'quit' to exit)")
    while True:
        user_input = input("\nYour question: ")
        
        if user_input.lower() == 'quit':
            print("Goodbye!")
            break
            
        print("\nResponse: ")
        # Remove callbacks from here since they're now in the LLM
        response = chain.invoke(
            {"question": user_input}
        )
        print()  # Add newline after response

if __name__ == "__main__":
    main()
