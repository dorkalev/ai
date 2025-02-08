#!/usr/bin/env python3
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence, Literal
import operator

load_dotenv()

# Initialize model
llm = ChatOpenAI(model="gpt-4")

# Define state type
class AgentState(TypedDict):
    messages: Annotated[Sequence[HumanMessage | AIMessage], operator.add]

def router(state: AgentState) -> dict:
    """Route the conversation to the appropriate agent based on the content."""
    messages = state["messages"]
    last_message = messages[-1].content
    
    # Ask LLM to classify the message
    classification_prompt = f"""Classify the following user message into one of these categories:
    - general_chat: for general conversation
    - math_agent: for mathematical calculations
    - code_agent: for programming related questions
    
    User message: {last_message}
    
    Response (just the category name):"""
    
    print("\n[ROUTER] Sending prompt to LLM:")
    print(classification_prompt)
    
    response = llm.invoke([HumanMessage(content=classification_prompt)])
    next_agent = response.content.strip().lower()
    return {"messages": messages, "next": next_agent}

def general_chat(state: AgentState) -> dict:
    """Handle general conversation."""
    messages = state["messages"]
    print("\n[GENERAL CHAT] Message history:")
    for msg in messages:
        print(f"{'User' if isinstance(msg, HumanMessage) else 'AI'}: {msg.content}")
    
    response_content = ""
    for chunk in llm.stream([messages[-1]]):
        content = chunk.content
        print(content, end="", flush=True)
        response_content += content
    print()
    return {"messages": messages + [AIMessage(content=response_content)], "next": END}

def math_agent(state: AgentState) -> dict:
    """Handle mathematical queries."""
    messages = state["messages"]
    math_prompt = "You are a mathematical expert. Please solve the following problem: " + messages[-1].content
    
    print("\n[MATH AGENT] Message history:")
    for msg in messages:
        print(f"{'User' if isinstance(msg, HumanMessage) else 'AI'}: {msg.content}")
    print("\n[MATH AGENT] Sending prompt to LLM:")
    print(math_prompt)
    
    response_content = ""
    for chunk in llm.stream([HumanMessage(content=math_prompt)]):
        content = chunk.content
        print(content, end="", flush=True)
        response_content += content
    print()
    return {"messages": messages + [AIMessage(content=response_content)], "next": END}

def code_agent(state: AgentState) -> dict:
    """Handle programming related queries."""
    messages = state["messages"]
    code_prompt = "You are a programming expert. Please help with the following: " + messages[-1].content
    
    print("\n[CODE AGENT] Message history:")
    for msg in messages:
        print(f"{'User' if isinstance(msg, HumanMessage) else 'AI'}: {msg.content}")
    print("\n[CODE AGENT] Sending prompt to LLM:")
    print(code_prompt)
    
    response_content = ""
    for chunk in llm.stream([HumanMessage(content=code_prompt)]):
        content = chunk.content
        print(content, end="", flush=True)
        response_content += content
    print()
    return {"messages": messages + [AIMessage(content=response_content)], "next": END}

# Build the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("router", router)
workflow.add_node("general_chat", general_chat)
workflow.add_node("math_agent", math_agent)
workflow.add_node("code_agent", code_agent)

# Add edges
workflow.set_entry_point("router")

# Add conditional edges from router
workflow.add_conditional_edges(
    "router",
    lambda x: x["next"],
    {
        "general_chat": "general_chat",
        "math_agent": "math_agent",
        "code_agent": "code_agent",
    }
)

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
