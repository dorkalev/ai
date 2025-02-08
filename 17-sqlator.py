#!/usr/bin/env python3

from flask import Flask, request, send_from_directory
from flask_sse import sse
import time
import sqlparse
import sqlite3
import re

from langchain_ollama import OllamaLLM
from langchain_openai import ChatOpenAI
# from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate

from dotenv import load_dotenv
from mako.template import Template

load_dotenv()

# llm = OllamaLLM(model="llama2")
gpt4 = ChatOpenAI(model="gpt-4")

user_prompt = ChatPromptTemplate.from_template("""
* The tables in the database are: [{tables}]
* Convert the following text to sqlite3 command wrapped in <sql> tags: {question}
* Do your best to make the sql correct and complete.
""")

verifier_prompt = ChatPromptTemplate.from_template("""
* The tables in the database are: {tables}
* does the following sql makes sense for sqlite3: {sql}
* If it contains insert to a table that does not exist then modify it to create the table first
* if it does, return the sql wrapped in <sql> tags
* if it doesn't, return the sql that fixes it in <sql> tags
* if there is an error, return the error message wrapped in <error> tags
* make sure to avoid "sqlite3.OperationalError: table users has 4 columns but 1 values were supplied" 
* never create table with hard constraints, always allow nulls
* Don't return any other text, explanations or comments
""")

user_chain = {
  "question": RunnablePassthrough(),
  "tables": lambda _: get_tables(True)
} | user_prompt | gpt4

verifier_chain = {
  "sql": RunnablePassthrough(),
  "tables": lambda _: get_tables(True)
} | verifier_prompt | gpt4


app = Flask(__name__)
app.config["REDIS_URL"] = "redis://localhost"
app.register_blueprint(sse, url_prefix='/stream')

def get_tables_content():
  conn = sqlite3.connect('example.db')
  c = conn.cursor()
  result = {}
  tables = get_tables(True)
  print(tables)
  for table in tables:
    c.execute(f"SELECT * FROM {table}")
    result[table] = c.fetchall()
  conn.close()
  return result

def get_tables(simple = False):
  conn = sqlite3.connect('example.db')
  c = conn.cursor()
  c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT IN ('sql_statements', 'sqlite_sequence')")
  tables = [table[0] for table in c.fetchall()]
  if simple:
    conn.close()
    return tables
  else:
    table_structures = {}
    for table_name in tables:
      c.execute(f"PRAGMA table_info({table_name})")
      columns = c.fetchall()
      table_structures[table_name] = columns
    conn.close()
    return table_structures

def init_db():
  conn = sqlite3.connect('example.db')
  c = conn.cursor()
  # Create table if it doesn't exist
  c.execute('''CREATE TABLE IF NOT EXISTS sql_statements
        (id INTEGER PRIMARY KEY AUTOINCREMENT, statement TEXT, type TEXT)''')
  # Query all tables in the database
  
  conn.commit()
  conn.close()

def extract_sql(text):
  if '<error>' in text:
    return ('error', re.search(r'<error>(.*?)</error>', text).group(1).strip())
  match = re.search(r'<sql>(.*?)</sql>', text, re.DOTALL)
  print(match)
  return ('sql', match.group(1).strip()) if match else (None, None)

def routi(f):
  joined_text = ''.join(f)
  sql_code = extract_sql(joined_text)[1]
  if sql_code:
    parsed = sqlparse.parse(sql_code)
    for statement in parsed:
      statement_type = statement.get_type()
      conn = sqlite3.connect('example.db')
      c = conn.cursor()
      yield f"data: \nVerifying SQL...\n"
      
      r0 = verifier_chain.stream(sql_code)
      f2 = []
      print('joe')
      for chunk in r0:
        f2.append(chunk.content)
        yield f"data: {chunk.content}\n\n"

      r2 = extract_sql(''.join(f2))
      
      if r2[0] == 'error':
        yield f"data: Error: {r2[1]}\n\n"
      else:
        sql_code2 = r2[1]
        c.execute("INSERT INTO sql_statements (statement, type) VALUES (?, ?)", (sql_code2, statement_type))
        conn.commit()
        yield f"data: Executing SQL...\n\n".encode('utf-8')
        
        c.execute(sql_code2)
        conn.commit()
        conn.close()
        
        if sql_code2 != sql_code:
          yield f"data: Modified SQL: {sql_code2}\n\n".encode('utf-8')
        else:
          yield f"data: Success\n\n".encode('utf-8')

@app.route('/')
def index():
  template = Template(filename='17-index.html')
  return template.render(tables=get_tables(), tables_content=get_tables_content())

@app.route('/respond')
def respond():
  question = request.args.get('question', '')
  f = []
  
  def generate():
    for chunk in user_chain.stream(question):    
      f.append(chunk.content)
      yield f"data: {chunk.content}\n\n".encode('utf-8')  
    for chunk in routi(f):
      yield chunk
    
  return app.response_class(
    generate(),
    mimetype='text/event-stream',
    headers={
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive'
    }
  )

if __name__ == '__main__':
  init_db()
  app.run(port=3000, debug=True)
