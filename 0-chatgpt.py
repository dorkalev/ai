#!/usr/bin/env python3
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

def main():
    print("Welcome to the GPT-4 Chat Interface! (Type 'quit' to exit)")
    while True:
        user_input = input("\nYour question: ")
        
        if user_input.lower() == 'quit':
            break
            
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": user_input}],
                temperature=0.7
            )
            print("\nResponse:", response.choices[0].message.content)
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
