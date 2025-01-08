from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(model="gpt-4", temperature=0.7)

prompt = PromptTemplate(
    input_variables=["question"],
    template="Please answer the following question: {question}"
)

chain = LLMChain(llm=llm, prompt=prompt)

def main():
    print("Welcome to the GPT-4 Chat Interface! (Type 'quit' to exit)")
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
