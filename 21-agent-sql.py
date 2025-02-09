#!/usr/bin/env python3

# pip install python-dotenv
# pip install langchain-openai
# pip install langchain
# pip install langgraph-core
# pip install typing
# pip install sqlite3 # usually comes with Python

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence, Literal
import operator
import sqlite3
import threading
import sys
import itertools
import time

load_dotenv()

# Initialize model
llm = ChatOpenAI(model="gpt-4")

# Define state type
class AgentState(TypedDict):
    messages: Annotated[Sequence[HumanMessage | AIMessage], operator.add]

def invoke_with_loader(llm, messages):
    """Invoke LLM with a loading animation."""
    stop_spinner = threading.Event()
    spinner_thread = threading.Thread(target=spin_loader, args=(stop_spinner,))
    spinner_thread.start()
    
    try:
        response = llm.invoke(messages)
        return response.content
    finally:
        stop_spinner.set()
        spinner_thread.join()
        sys.stdout.write('\b \b')  # Clear the spinner
        sys.stdout.flush()

def create_spinner():
    """Create a terminal spinner animation."""
    spinner = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
    return spinner

def spin_loader(stop):
    """Animate the spinner while waiting."""
    spinner = create_spinner()
    while not stop.is_set():
        sys.stdout.write(next(spinner))
        sys.stdout.flush()
        sys.stdout.write('\b')
        time.sleep(0.1)

def router(state: AgentState) -> dict:
    """Route the conversation to the appropriate agent based on the content."""
    messages = state["messages"]
    last_message = messages[-1].content
    
    # Check for info command first
    if last_message.lower().strip() == "info":
        return {"messages": messages, "next": "info_agent"}
    
    # First, determine if the question requires historical context
    history_prompt = f"""Analyze if the following message requires previous conversation history to be properly answered. 
    Consider things like:
    - References to previous questions or answers
    - Use of words like "that", "it", "this", "those", etc.
    - Questions that build upon previous context
    
    Message: {last_message}
    
    Respond with only 'yes' or 'no':"""
    
    needs_history = invoke_with_loader(llm, [HumanMessage(content=history_prompt)]).strip().lower() == 'yes'
    
    # If historical context is needed, create a summary
    if needs_history and len(messages) > 1:
        summary_prompt = f"""Summarize the relevant context from this conversation history. Focus only on information needed to understand the latest question.
        
        Conversation:
        {chr(10).join(f"{'User' if isinstance(msg, HumanMessage) else 'AI'}: {msg.content}" for msg in messages[:-1])}
        
        Latest question: {last_message}
        
        Summary:"""
        
        context_summary = invoke_with_loader(llm, [HumanMessage(content=summary_prompt)]).strip()
        last_message = f"Context: {context_summary}\n\nQuestion: {last_message}"
    
    classification_prompt = f"""Classify the following user message into one of these categories:
    - general_chat: for general conversation
    - math_agent: for mathematical calculations
    - code_agent: for programming related questions
    - sql_agent: for questions about customer data or database queries
    
    User message: {last_message}
    
    Response (just the category name):"""
    
    print("\n[ROUTER] Sending prompt to LLM:")
    print(classification_prompt)
    
    next_agent = invoke_with_loader(llm, [HumanMessage(content=classification_prompt)]).strip().lower()
    
    if needs_history and len(messages) > 1:
        messages = messages[:-1] + [HumanMessage(content=last_message)]
    
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

def info_agent(state: AgentState) -> dict:
    """Display SQLite database schema and content."""
    
    messages = state["messages"]
    print("\n[INFO AGENT] Database Information:")
    
    try:
        conn = sqlite3.connect('example.db')
        cursor = conn.cursor()
        
        # Get table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT IN ('sql_statements', 'sqlite_sequence');")
        tables = cursor.fetchall()
        
        info_output = []
        info_output.append("Database Schema:")
        for table in tables:
            table_name = table[0]
            info_output.append(f"\nTable: {table_name}")
            
            # Get schema for each table
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            info_output.append("Columns:")
            for col in columns:
                info_output.append(f"  - {col[1]} ({col[2]})")
            
            # Get content for each table
            cursor.execute(f"SELECT * FROM {table_name};")
            rows = cursor.fetchall()
            info_output.append("\nContent:")
            for row in rows:
                info_output.append(f"  {row}")
        
        info_text = "\n".join(info_output)
        # print(info_text)
        # print('--------------------------------')
        conn.close()
        return {"messages": messages + [AIMessage(content=info_text)], "next": END}
        
    except sqlite3.Error as e:
        error_msg = f"SQLite error: {str(e)}"
        print(error_msg)
        return {"messages": messages + [AIMessage(content=error_msg)], "next": END}

def sql_agent(state: AgentState) -> dict:
    """Handle SQL queries for customer data."""
    messages = state["messages"]
    sql_prompt = """You are a SQL expert. Convert the following request into a SQLite query.
    Only respond with the SQL query, nothing else.
    Request: """ + messages[-1].content
    
    print("\n[SQL AGENT] Message history:")
    for msg in messages:
        print(f"{'User' if isinstance(msg, HumanMessage) else 'AI'}: {msg.content}")
    
    # Get SQL query from LLM
    query = invoke_with_loader(llm, [HumanMessage(content=sql_prompt)]).strip()
    print("\n[SQL AGENT] Generated SQL query:")
    print(query)
    
    try:
        conn = sqlite3.connect('example.db')
        cursor = conn.cursor()
        
        # Execute the query and commit (safe for all query types)
        cursor.execute(query)
        conn.commit()
        
        # Try to fetch results (will work for SELECT, do nothing for others)
        try:
            results = cursor.fetchall()
            
            # Format results
            if not results:
                response_content = "No results found."
            else:
                # Get column names
                column_names = [description[0] for description in cursor.description]
                
                # Format as readable output
                output = ["Results:"]
                output.append("Columns: " + " | ".join(column_names))
                for row in results:
                    output.append(" | ".join(str(item) for item in row))
                response_content = "\n".join(output)
        except:
            # For non-SELECT queries
            affected_rows = cursor.rowcount
            response_content = f"Query executed successfully. Affected rows: {affected_rows}"
        
        conn.close()
        
    except sqlite3.Error as e:
        response_content = f"Database error: {str(e)}"
    
    return {"messages": messages + [AIMessage(content=response_content)], "next": END}

# Build the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("router", router)
workflow.add_node("general_chat", general_chat)
workflow.add_node("math_agent", math_agent)
workflow.add_node("code_agent", code_agent)
workflow.add_node("info_agent", info_agent)
workflow.add_node("sql_agent", sql_agent)

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
        "info_agent": "info_agent",
        "sql_agent": "sql_agent",
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
