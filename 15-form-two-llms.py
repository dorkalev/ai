#!/usr/bin/env python3

from flask import Flask, request, send_from_directory
from flask_sse import sse
import time

from langchain_ollama import OllamaLLM
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from itertools import zip_longest

load_dotenv()

gpt4 = ChatOpenAI(model="gpt-4")


from dotenv import load_dotenv

load_dotenv()

llm = OllamaLLM(model="llama2")

prompt = ChatPromptTemplate.from_template("""
{question}
""")


chain  = { "question": RunnablePassthrough() } | prompt | llm
chain2 = { "question": RunnablePassthrough() } | prompt | gpt4

app = Flask(__name__)
app.config["REDIS_URL"] = "redis://localhost"
app.register_blueprint(sse, url_prefix='/stream')

@app.route('/')
def index():
    return send_from_directory('.', '15-index.html')

@app.route('/respond')
def respond():
    question = request.args.get('question', '')

    def generate_combined():
        # Create iterators for both streams
        stream1 = chain.stream(question)
        stream2 = chain2.stream(question)

        # Use zip_longest to iterate over both streams
        for chunk1, chunk2 in zip_longest(stream1, stream2, fillvalue=None):
            if chunk1 is not None:
                # Replace \n with <br> before sending to browser
                chunk1_formatted = str(chunk1).replace('\n', '<br>')
                yield f"data: 1.{chunk1_formatted}\n\n"
            if chunk2 is not None:
                # Replace \n with <br> before sending to browser
                chunk2_formatted = chunk2.content.replace('\n', '<br>')
                yield f"data: 2.{chunk2_formatted}\n\n"

    return app.response_class(
        generate_combined(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        }
    )

if __name__ == '__main__':
    app.run(port=3000, debug=True)

