#!/usr/bin/env python3

from flask import Flask, request, send_from_directory
from flask_sse import sse
import time

from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough

from dotenv import load_dotenv

load_dotenv()

llm = OllamaLLM(model="llama2")

prompt = PromptTemplate(
    input_variables=["question"],
    template="Please answer the following question: {question}"
)

chain = {"question": RunnablePassthrough()} | prompt | llm

app = Flask(__name__)
app.config["REDIS_URL"] = "redis://localhost"
app.register_blueprint(sse, url_prefix='/stream')

@app.route('/')
def index():
    return send_from_directory('.', '14-index.html')

@app.route('/respond')
def respond():
    question = request.args.get('question', '')

    # response = chain.invoke(question)
    # for chunk in chain.stream(question):
    #         print(chunk.content, end="", flush=True)

    def generate():
      for chunk in chain.stream(question):      
        yield f"data: {chunk}\n\n"

    return app.response_class(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        }
    )

if __name__ == '__main__':
    app.run(port=3000, debug=True)

