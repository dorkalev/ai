#!/usr/bin/env python3
import os, shutil, sys
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import justext
import requests
import hashlib
import re
from langchain_ollama import OllamaLLM
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from asyncio import create_task, gather, sleep, run

from urllib.parse import urlparse, urlunparse

load_dotenv()
global_url = ["https://daff.co.il"]

llm = OllamaLLM(model="llama3.2") # or llama2

prompt = PromptTemplate(
    input_variables=["question"],
    template="answer in Hebrew what is this story about: {question}"
)

chain = {"question": RunnablePassthrough()} | prompt | llm

tasks = []

def prepare_file(url):
    parsed_url = urlparse(url)
    url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, '', '', ''))
    f = hashlib.sha1(url.encode()).hexdigest()[:20]
    if not any(os.path.exists(os.path.join(dir, f)) for dir in ['TODO', 'DOING', 'DONE', 'EMPTY']):
        with open(os.path.join('TODO', f), 'w', encoding='utf-8') as file:
            file.write(url)

def crawl_and_move():
    while (files := os.listdir('TODO')):
        filename = files.pop()
        todo_path = os.path.join('TODO', filename)
        with open(todo_path, 'r', encoding='utf-8') as file:
            url = file.read().strip()
        
        process_path, dest_path, err_path, empty_path, summary_path = (os.path.join(dir, filename) for dir in ['DOING', 'DONE', 'ERR', 'EMPTY', 'SUMMARY'])
        shutil.move(todo_path, process_path)
        try:
            if not any(url.startswith(g_url) for g_url in global_url): continue

            response = requests.get(url)
            paragraphs = justext.justext(response.content, justext.get_stoplist("Hebrew"))

            title, main_content = "", ""
            for paragraph in paragraphs:
                if paragraph.class_type == 'heading':
                    title = paragraph.text
                if not paragraph.is_boilerplate:
                    main_content += paragraph.text + "\n"
            # print(url, "Title:", title, "Main Content:", main_content, sep='\n')
                        
            with open(process_path, 'w', encoding='utf-8') as file:
                file.write(f"{url}\n{title}\n{main_content}")
            soup = BeautifulSoup(response.content, 'html.parser')

            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('/'): href = url + href
                if href.startswith('http'): prepare_file(href)
            if not title and not main_content.strip():
                shutil.move(process_path, empty_path)
                continue
            # Add the generate_summary task to the global array
            tasks.append(create_task(generate_summary(title, main_content, summary_path)))
            shutil.move(process_path, dest_path)
        except Exception as e:
            print(f"Error processing {url}: {e}")
            shutil.move(process_path, err_path)

async def generate_summary(title, main_content, summary_path):
    try:
        summary = await chain.ainvoke(title + "\n" + main_content)
        with open(summary_path, 'w', encoding='utf-8') as summary_file:
            summary_file.write(summary)
    except Exception as e:
        print(f"Error generating summary: {e}")

async def main():
    for dir in ['TODO', 'DOING', 'DONE', 'ERR', 'EMPTY', 'SUMMARY']:
        if 'restart' in sys.argv:
            shutil.rmtree(dir, ignore_errors=True)
        os.makedirs(dir, exist_ok='restart' not in sys.argv)
    os.system('mv DOING/* TODO/')
    if not os.listdir('TODO'):
        prepare_file(global_url[0])
    
    done_files = set(os.listdir('DONE'))
    summary_files = set(os.listdir('SUMMARY'))

    files_to_summarize = done_files - summary_files

    for filename in files_to_summarize:
        done_path = os.path.join('DONE', filename)
        summary_path = os.path.join('SUMMARY', filename)
        
        with open(done_path, 'r', encoding='utf-8') as file:
            content = file.read().strip()
            lines = content.split('\n')
            url = lines[0]
            title = lines[1] if len(lines) > 1 else ""
            main_content = "\n".join(lines[2:]) if len(lines) > 2 else ""
        
        # Schedule the generate_summary task
        tasks.append(create_task(generate_summary(title, main_content, summary_path)))
    
    # Await all tasks
    await gather(*tasks)
    crawl_and_move()

if __name__ == "__main__":
    # Use asyncio.run() only if not already in an event loop
    try:
        run(main())
    except RuntimeError as e:
        if "asyncio.run() cannot be called from a running event loop" in str(e):
            # If already in an event loop, use an alternative method
            import nest_asyncio
            nest_asyncio.apply()
            run(main())
