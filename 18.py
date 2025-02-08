#!/usr/bin/env python3

from flask import Flask, request, render_template, send_from_directory
from flask_sse import sse
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence
from mako.template import Template
import operator

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config["REDIS_URL"] = "redis://localhost"
app.register_blueprint(sse, url_prefix='/stream')

# Initialize the LLM
llm = ChatOpenAI(model="gpt-4")

# Define the state type
class AgentState(TypedDict):
  messages: Annotated[Sequence[HumanMessage | AIMessage], operator.add]

# Create the chat prompt
prompt = ChatPromptTemplate.from_messages([
  ("system", "You are a helpful AI assistant."),
  MessagesPlaceholder(variable_name="messages"),
  ("human", "{input}")
])

# Define the agent function
def agent(state: AgentState, input_text: str):
  messages = state["messages"]
  
  # Invoke the LLM
  response = llm.invoke(
    prompt.format_messages(messages=messages, input=input_text)
  )
  
  # Return the updated state
  return {"messages": messages + [HumanMessage(content=input_text), AIMessage(content=response.content)]}

# Create the graph
workflow = StateGraph(AgentState)

# Add the node
workflow.add_node("agent", agent)

# Set the starting node
workflow.set_entry_point("agent")

# Add the edge from agent back to agent
workflow.add_edge("agent", END)

# Compile the graph
app_graph = workflow.compile()
@app.route('/<path:filename>.js')
def serve_js(filename):
    return send_from_directory('.', f'{filename}.js')

@app.route('/')
def index():
  template = Template(filename='18index.html')
  
  # tables = get_tables()
  return template.render() #tables=tables)

@app.route('/chat', methods=['POST'])
def chat():
  message = request.json.get('message', '')
  
  def generate():
    # Initialize or get the chat history
    chat_history = request.json.get('history', [])
    messages = []
    
    # Convert history to message objects
    for msg in chat_history:
      if msg['role'] == 'human':
        messages.append(HumanMessage(content=msg['content']))
      else:
        messages.append(AIMessage(content=msg['content']))
    
    # Create initial state
    state = {"messages": messages}
    
    # Run the graph
    result = app_graph.invoke({
      "messages": messages,
      "input": message
    })
    
    # Get the last AI message
    last_message = result["messages"][-1].content
    
    yield f"data: {last_message}\n\n".encode('utf-8')
  
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