#!/usr/bin/env python3

from flask import Flask, request, send_from_directory
from flask_sse import sse
import time

from langchain_ollama import OllamaLLM
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from dotenv import load_dotenv

load_dotenv()

llm_llama = OllamaLLM(model="llama2")
llm_gpt4 = ChatOpenAI(model="gpt-4o")

prompt = ChatPromptTemplate.from_template("""
* You are a helpful assistant.
* You are given a text and a user prompt.
* You are a poetry writing assistant and you are writing in Hebrew.
* The user prompt is: {question}
* Apply the user prompt to the text: {selectedText}
"""
)

chain_llama = RunnablePassthrough() | prompt | llm_llama
chain_gpt4  = RunnablePassthrough() | prompt | llm_gpt4

app = Flask(__name__)
app.config["REDIS_URL"] = "redis://localhost"
app.register_blueprint(sse, url_prefix='/stream')

@app.route('/')
def index():
    return send_from_directory('.', '16-rte.html')

@app.route('/respond')
def respond():
    model = request.args.get('model', 'gpt-4')

    chain = chain_llama if model == 'llama2' else chain_gpt4
    params = {k: request.args.get(k, '') for k in ['question', 'selectedText']}

    def generate():
      for chunk in chain.stream(params):
        if model == 'gpt4':
            chunk = chunk.content      
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
