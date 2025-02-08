#!/usr/bin/env python3
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence
import operator

load_dotenv()

# Initialize model
llm = ChatOpenAI(model="gpt-4")

# Define state type
class AgentState(TypedDict):
    messages: Annotated[Sequence[HumanMessage | AIMessage], operator.add]

def agent_function(state: AgentState) -> dict:
    """Agent function that processes user input."""
    messages = state["messages"]
    response = llm.invoke([messages[-1]])
    return {"messages": messages + [AIMessage(content=response.content)], "next": END}

# Build the graph
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_function)
workflow.set_entry_point("agent")

dialogue_manager = workflow.compile()

# Interactive loop
if __name__ == "__main__":
    messages = []
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting...")
            break
        
        messages.append(HumanMessage(content=user_input))
        response = dialogue_manager.invoke({"messages": messages})
        messages = response["messages"]
        ai_response = messages[-1].content
        print(f"AI: {ai_response}")
