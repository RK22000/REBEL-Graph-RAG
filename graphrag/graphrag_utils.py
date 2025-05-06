import networkx as nx
import nx_arangodb as nxadb

from arango import ArangoClient

import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from random import randint
import re

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_deepseek import ChatDeepSeek
from langchain_community.graphs import ArangoGraph
from langchain_community.chains.graph_qa.arangodb import ArangoGraphQAChain
from langchain_core.tools import tool
import os

from dotenv import load_dotenv

import requests
import json
from properties import *

load_dotenv()

DEEPSEEK_API_KEY=os.getenv("DEEPSEEK_API_KEY")
ARANGO_PASS=os.getenv("ADBPASS")


def chunkify(text, chunk_size=500, overlap=50 ):
    text = re.sub(r'\s+', ' ', text.strip())
    sentences = re.split('(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = []
    current_length = 0
    last_sentences = []  
    for sentence in sentences:
        sentence_length = len(sentence)
        if current_length + sentence_length > chunk_size and current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(chunk_text)
            overlap_size = 0
            overlap_sentences = []
            for s in reversed(current_chunk):
                if overlap_size + len(s) > overlap:
                    break
                overlap_sentences.insert(0, s)
                overlap_size += len(s) + 1 
            current_chunk = overlap_sentences
            current_length = overlap_size
        current_chunk.append(sentence)
        current_length += sentence_length + 1 
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    return chunks

def rebel_api_call(chunks):
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'chunks': chunks
    }
    
    try:
        response = requests.post(REBEL_URL, headers=headers, json=payload)
        response.raise_for_status()  
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None

def send_to_rebel_kb(chunks):
    url = 'https://rebel-server-139095284696.us-central1.run.app/kb'
    
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'chunks': chunks
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status() 
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None

def text2kb(input_text):
    chunks = chunkify(input_text, chunk_size=500, overlap=50)
    result = rebel_api_call(chunks)
    
    if result:
        return result
    

llm = ChatDeepSeek(temperature=0, model_name="deepseek-chat", api_key=DEEPSEEK_API_KEY)
db = ArangoClient(hosts=ARANGO_URL).db(username="root", password=ARANGO_PASS, verify=True)
arango_graph = ArangoGraph(db)

@tool
def text_to_aql_to_text(query: str, eval: bool = False):
    """
    Use this tool when you need to query the ArangoDB graph database directly using AQL (ArangoDB Query Language).
    This is best for:
    - Finding specific nodes or relationships
    - Querying based on node properties
    - Traversing the graph with specific patterns
    - Getting direct answers about graph structure
    
    Args:
        query: A natural language query about the graph data
    Returns:
        The result of the AQL query in natural language
    """
    chain = ArangoGraphQAChain.from_llm(
    	llm=llm,
    	graph=arango_graph,
    	verbose=True,
        return_aql_query=True,
        allow_dangerous_requests=True
    )
    print("In text_to_aql_to_text...")
    final_query = f"""I have a NetworkX Graph called `G_adb`. It has the following schema: {arango_graph.schema}

    I have the following question: {query}.

    Write an ArangoDB query to answer the question based on the graph schema. Be very specific while writing the query. If the entities and relationships that match the user question exist, use that information.

    The DB has nodes in this form: "india_node/92" where 92 is the node ID. you will have to ensure that you are accessing node names while writing the query. Access node names by using "node.name" - name is a parameter. You have to do this without fail. 

    Follow this example:
    Natural language question: "What countries does India share a border with?"
    AQL query: "WITH india_node, india_node_to_india_node
FOR start IN india_node
  FILTER start.name == "India"
  FOR v, e, p IN 1..1 OUTBOUND start india_node_to_india_node
    FILTER e.relationship IN ['shares border with', 'borders']
    RETURN DISTINCT v.name"
    
    These are the relationships in the graph. Use these in your query generation.

    ['capital of', 'is capital of', 'has official language',
       'flows through', 'is located in', 'celebrates',
       'shares border with', 'borders', 'is from', 'is famous for',
       'has traditional dance form', 'was from', 'fought for',
       'started in', 'was led by', 'took place in', 'led',
       'is associated with', 'was significant in', 'was', 'served in',
       'was known for', 'was based in', 'was established in', 'was for',
       'was headquartered in', 'was introduced in', 'was related to',
       'was implemented in', 'became prominent in', 'ended in',
       'established first factory in', 'gained Diwani rights in',
       'happened in', 'arrived in India in', 'was reversed in',
       'was founded during', 'started during', 'was introduced by',
       'was dominated by', 'was reorganized by', 'was established by',
       'was the founder of', 'battled in', 'defeated', 'reigned from',
       'reigned till', 'was succeeded by', 'was the son of', 'lost to',
       'went into exile in', 'reclaimed throne in', 'ascended throne in',
       'introduced', 'built', 'was married to', 'titled his wife',
       'patronized', 'was imprisoned by', 'imprisoned',
       'expanded empire to', 'reimposed', 'was the last powerful',
       'was fought between', 'resulted in', 'was won by', 'established',
       'led to', 'secured', 'was inconclusive in outcome', 'showed',
       'was part of', 'fought prolonged war in', 'struggled against',
       'challenged', 'invasively attacked', 'plundered']

    Here are the head node names: 

        ['Maharashtra', 'Mumbai', 'Karnataka', 'Bengaluru', 'Tamil Nadu',
       'Chennai', 'Kerala', 'Thiruvananthapuram', 'Andhra Pradesh',
       'Amaravati', 'Uttar Pradesh', 'Lucknow', 'Bihar', 'Patna',
       'West Bengal', 'Kolkata', 'Gujarat', 'Gandhinagar', 'Rajasthan',
       'Jaipur', 'Madhya Pradesh', 'Bhopal', 'Punjab', 'Chandigarh',
       'Haryana', 'Odisha', 'Bhubaneswar', 'Assam', 'Dispur', 'Jharkhand',
       'Ranchi', 'Chhattisgarh', 'Raipur', 'Uttarakhand', 'Dehradun',
       'Himachal Pradesh', 'Shimla', 'Goa', 'Panaji', 'Ganges', 'Yamuna',
       'Brahmaputra', 'Godavari', 'Krishna', 'Narmada', 'Tapi',
       'Mahanadi', 'Kaveri', 'Indus', 'Himalayas', 'Western Ghats',
       'Eastern Ghats', 'Aravalli Range', 'Vindhya Range',
       'Satpura Range', 'Nilgiri Hills', 'Shivalik Hills', 'India',
       'Taj Mahal', 'Red Fort', 'Qutub Minar', 'Gateway of India',
       'Hawa Mahal', 'Victoria Memorial', 'Charminar', 'Golden Temple',
       'Bal Gangadhar Tilak', 'Lata Mangeshkar', 'Sachin Tendulkar',
       'Rabindranath Tagore', 'Satyajit Ray', 'Sourav Ganguly',
       'M.S. Subbulakshmi', 'A.R. Rahman', 'Viswanathan Anand',
       'Mahatma Gandhi', 'Sardar Patel', 'Narendra Modi',
       'Amitabh Bachchan', 'Jawaharlal Nehru', 'Kalpana Chawla',
       'A.P.J. Abdul Kalam', 'Mammootty', 'Shashi Tharoor',
       'Bhagat Singh', 'Diljit Dosanjh', 'Kapil Dev', 'Mirabai',
       'Prithviraj Chauhan', 'Rani Padmini', 'Fatehpur Sikri',
       'Amber Fort', 'Ajanta Caves', 'Brihadeeswarar Temple',
       'Meenakshi Temple', 'Konark Sun Temple', 'Jagannath Temple',
       'Hampi', 'Mysore Palace', 'Rani ki Vav', 'Somnath Temple',
       'Gopal Krishna Gokhale', 'Vinayak Damodar Savarkar',
       'Subhash Chandra Bose', 'Khudiram Bose', 'Rash Behari Bose',
       'Sardar Vallabhbhai Patel', 'Dadabhai Naoroji',
       'Chandra Shekhar Azad', 'Rani Lakshmibai', 'Jayaprakash Narayan',
       'Rajendra Prasad', 'Anugrah Narayan Sinha', 'Lala Lajpat Rai',
       'Udham Singh', 'Subramania Bharati', 'V.O. Chidambaram Pillai',
       'C. Rajagopalachari', 'K. Kelappan', 'A.K. Gopalan',
       'Vakkom Moulavi', 'Alluri Sitarama Raju', 'Tanguturi Prakasam',
       'Potti Sreeramulu', 'Gopabandhu Das', 'Biju Patnaik',
       'Utkal Gourav Madhusudan Das', 'Non-Cooperation Movement',
       'Quit India Movement', 'Swadeshi Movement',
       'Civil Disobedience Movement', 'Champaran Satyagraha',
       'Kheda Satyagraha', 'Salt March', 'Kakori Conspiracy',
       'Ram Prasad Bismil', 'Jallianwala Bagh Massacre', 'General Dyer',
       'Chauri Chaura Incident', 'Sabarmati Ashram', 'Jallianwala Bagh',
       'Cellular Jail', 'Aga Khan Palace', 'India Gate', 'Champaran',
       'Dandi', 'Warren Hastings', 'Lord Cornwallis', 'Lord Wellesley',
       'Lord William Bentinck', 'Lord Dalhousie', 'Lord Canning',
       'Lord Curzon', 'Lord Mountbatten', 'Robert Clive', 'James Outram',
       'Lord Kitchener', 'Thomas Macaulay', 'Charles Wood',
       'John Lawrence', 'William Sleeman', 'East India Company',
       'Indian Civil Service', 'Indian Police Service', 'Indian Army',
       'Presidency Colleges', 'Railway System', 'Telegraph System',
       'Postal System', 'Permanent Settlement', 'Doctrine of Lapse',
       'Subsidiary Alliance', 'Divide and Rule', 'Ilbert Bill',
       'Rowlatt Act', 'Government of India Act', 'Indian Councils Act',
       'British Raj', 'Battle of Plassey', 'Battle of Buxar',
       'First War of Independence', 'Simon Commission', 'Cripps Mission',
       'Cabinet Mission', 'Partition of Bengal',
       'Indian National Congress', 'Muslim League', 'Indian Railways',
       'Indian Postal Service', 'English Education', 'Indian Police',
       'Babur', 'Humayun', 'Akbar', 'Jahangir', 'Shah Jahan', 'Aurangzeb',
       'Battle of Panipat (1526)', 'Battle of Khanwa (1527)',
       'Battle of Ghaghra (1529)', 'Battle of Chausa (1539)',
       'Battle of Kanauj (1540)', 'Second Battle of Panipat (1556)',
       'Battle of Haldighati (1576)', 'Battle of Samugarh (1658)',
       'Battle of Deorai (1659)', 'Battle of Satara (1700s)', 'Mughals',
       'Battle of Delhi (1737)', 'Marathas', 'Nadir Shah']

       Here are the tail nodes:
       ['Mumbai', 'Maharashtra', 'Bengaluru', 'Karnataka', 'Chennai',
       'Tamil Nadu', 'Thiruvananthapuram', 'Kerala', 'Amaravati',
       'Andhra Pradesh', 'Lucknow', 'Uttar Pradesh', 'Patna', 'Bihar',
       'Kolkata', 'West Bengal', 'Gandhinagar', 'Gujarat', 'Jaipur',
       'Rajasthan', 'Bhopal', 'Madhya Pradesh', 'Chandigarh', 'Punjab',
       'Haryana', 'Bhubaneswar', 'Odisha', 'Dispur', 'Assam', 'Ranchi',
       'Jharkhand', 'Raipur', 'Chhattisgarh', 'Dehradun', 'Uttarakhand',
       'Shimla', 'Himachal Pradesh', 'Panaji', 'Goa', 'Marathi',
       'Kannada', 'Tamil', 'Malayalam', 'Telugu', 'Hindi', 'Bengali',
       'Gujarati', 'Punjabi', 'Odia', 'Assamese', 'Konkani', 'Delhi',
       'Jammu and Kashmir', 'Rath Yatra', 'Ugadi', 'Hareli', 'Navratri',
       'Dasara', 'Pongal', 'Baisakhi', 'Durga Puja', 'Teej', 'Christmas',
       'Pakistan', 'China', 'Nepal', 'Bhutan', 'Bangladesh', 'Myanmar',
       'Telangana', 'Arunachal Pradesh', 'Nagaland', 'Manipur', 'Mizoram',
       'Tripura', 'Meghalaya', 'Vada Pav', 'Pav Bhaji', 'Puran Poli',
       'Rasgulla', 'Macher Jhol', 'Mishti Doi', 'Dosa', 'Idli', 'Dhokla',
       'Thepla', 'Khandvi', 'Kebabs', 'Biryani', 'Jalebi', 'Appam',
       'Puttu', 'Karimeen Pollichathu', 'Makki di Roti', 'Sarson da Saag',
       'Butter Chicken', 'Dal Baati Churma', 'Ghewar', 'Laal Maas',
       'Lavani', 'Koli', 'Gaudiya Nritya', 'Bharatanatyam', 'Karakattam',
       'Garba', 'Dandiya', 'Kathak', 'Raslila', 'Kathakali',
       'Mohiniyattam', 'Bhangra', 'Giddha', 'Ghoomar', 'Kalbelia',
       'Indian Independence', '1920', 'Mahatma Gandhi', 'Ahmedabad',
       'Non-Cooperation Movement', '1942', 'Quit India Movement', '1905',
       'Bal Gangadhar Tilak', 'Swadeshi Movement', '1930', 'Sabarmati',
       'Civil Disobedience Movement', '1917', 'Champaran',
       'Champaran Satyagraha', '1918', 'Kheda', 'Kheda Satyagraha',
       'Dandi', 'Salt March', '1925', 'Ram Prasad Bismil', 'Kakori',
       'Kakori Conspiracy', '1919', 'General Dyer', 'Amritsar',
       'Jallianwala Bagh Massacre', '1922', 'Local Protesters',
       'Chauri Chaura', 'Chauri Chaura Incident', 'Indian National Army',
       '1945', 'Andaman and Nicobar', 'Freedom Fighters', '1906',
       'British Raj', '1921', '1924', '1931', 'Governors-General', '1773',
       'First Governor-General', 'Calcutta', '1786',
       'Permanent Settlement', '1798', 'Subsidiary Alliance', '1828',
       'Abolition of Sati', '1848', 'Doctrine of Lapse', '1856',
       'First Viceroy', '1899', 'Partition of Bengal', '1947',
       'Last Viceroy', 'New Delhi', 'Military Officers', '1757',
       'Battle of Plassey', 'Bengal', '1857', 'Indian Rebellion',
       'Jallianwala Bagh', '1902', 'Army Reforms', 'Administrators',
       '1834', 'English Education', '1854', "Wood's Dispatch", 'London',
       '1864', 'Punjab Administration', 'Lahore', '1830',
       'Thuggee Suppression', 'Central India', '1600', 'Trading Company',
       '1858', 'Administrative Service', '1861', 'Police Force',
       'Military Force', '1817', 'Education', '1853', 'Transportation',
       'Bombay', '1851', 'Communication', '1793', 'Land Revenue',
       'Annexation Policy', 'India', 'Military Policy',
       'Political Policy', '1883', 'Judicial Reform', 'Repressive Law',
       'Constitutional Reform', 'Legislative Reform', 'Surat', '1765',
       '1764', '1928', '1946', '1911', 'British Rule', 'British',
       'Mughal Empire', 'Battle of Panipat', 'Ibrahim Lodi', '1526',
       '1530', 'Humayun', 'Babur', 'Shershah Suri', 'Persia', '1555',
       'Akbar', '1556', 'Second Battle of Panipat', 'Hemu', 'Din-i Ilahi',
       'Fatehpur Sikri', 'Jahangir', 'Mehrunissa', 'Nur Jahan',
       'painting', 'Shah Jahan', 'Taj Mahal', 'Red Fort', 'Jama Masjid',
       'Aurangzeb', 'Deccan', 'Jizya tax', '1707', 'Mughal ruler',
       'Babur and Ibrahim Lodi', 'Foundation of Mughal Empire', 'Panipat',
       'Babur and Rana Sanga', "Babur's control over North India",
       'Babur and Afghans', 'Humayun and Sher Shah Suri',
       'Sher Shah Suri', "Humayun's exile", 'Akbar and Hemu',
       "Akbar's throne", 'Akbar and Maharana Pratap',
       'Man Singh for Akbar', nan, 'Rajput resistance',
       'Aurangzeb and Dara Shikoh', 'War of Succession',
       'Aurangzeb and Shuja', "Aurangzeb's control over Mughal throne",
       'Aurangzeb and Marathas', 'Maratha guerrilla tactics',
       'Marathas and Mughals', 'Marathas', 'Mughal supremacy',
       'Delhi in 1739', 'Mughal army']
       
    """
    result = chain.invoke(final_query)
    if eval:
        return result["aql_query"]
    else:
        return str(result["result"])

@tool
def text_to_nx_algorithm_to_text(query):
    """
    Use this tool when you need to perform complex graph analysis or algorithms on the graph.
    This is best for:
    - Finding paths between nodes
    - Analyzing graph properties (centrality, clustering, etc.)
    - Performing graph traversals
    - Complex graph pattern matching
    - Graph metrics and statistics
    
    Args:
        query: A natural language query about graph analysis
    Returns:
        The result of the graph analysis in natural language
    """
    print("1) Generating NetworkX code")

    text_to_nx = llm.invoke(f"""
    I have a NetworkX Graph called `G_adb`. It has the following schema: {arango_graph.schema}

    I have the following graph analysis query: {query}.

    Generate the Python Code required to answer the query using the `G_adb` object. Make sure you are returning the names of the nodes (use `name`) instead of ID or key.

    Be very precise on the NetworkX algorithm you select to answer this query. Think step by step.

    Only assume that networkx is installed, and other base python dependencies.

    Always set the last variable as `FINAL_RESULT`, which represents the answer to the original query.

    Only provide python code that I can directly execute via `exec()`. Do not provide any instructions.

    Make sure that `FINAL_RESULT` stores a short & consice answer. Avoid setting this variable to a long sequence.

    Your code:
    """).content

    text_to_nx_cleaned = re.sub(r"^```python\n|```$", "", text_to_nx, flags=re.MULTILINE).strip()

    print('-'*10)
    print(text_to_nx_cleaned)
    print('-'*10)
    
    print("\n2) Executing NetworkX code")
    global_vars = {"G_adb": G_adb, "nx": nx}
    local_vars = {}

    try:
        exec(text_to_nx_cleaned, global_vars, local_vars)
        text_to_nx_final = text_to_nx
    except Exception as e:
        print(f"EXEC ERROR: {e}")
        return f"EXEC ERROR: {e}"

        # TODO: need a code correction mechanism
        # TODO: add attempt limit?
    print('-'*10)
    FINAL_RESULT = local_vars["FINAL_RESULT"]
    print(f"FINAL_RESULT: {FINAL_RESULT}")
    print('-'*10)

    print("3) Formulating final answer")

    nx_to_text = llm.invoke(f"""
        I have a NetworkX Graph called `G_adb`. It has the following schema: {arango_graph.schema}

        I have the following graph analysis query: {query}.

        I have executed the following python code to help me answer my query:

        ---
        {text_to_nx_final}
        ---

        The `FINAL_RESULT` variable is set to the following: {FINAL_RESULT}.

        Based on my original Query and FINAL_RESULT, generate a short and concise response to
        answer my query.

        Don't ask follow up questions like "Would you like more details...". This is very important. Just answer the question and stop at that.

        Your response:
    """).content

    return nx_to_text

tools = [text_to_aql_to_text, text_to_nx_algorithm_to_text]

def query_graph(query):
    print("In query_graph...")
    app = create_react_agent(llm, tools)
    final_state = app.invoke({"messages": [{"role": "user", "content": query}]})
    return final_state["messages"][-1].content
    