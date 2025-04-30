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
def text_to_aql_to_text(query: str):
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
        allow_dangerous_requests=True
    )
    final_query = f"""I have a NetworkX Graph called `G_adb`. It has the following schema: {arango_graph.schema}

    I have the following question: {query}.

    Write an ArangoDB query to answer the question based on the graph schema. Be very specific while writing the query. If the entities and relationships that match the user question exist, use that information.

    The DB has nodes in this form: "india_node/92" where 92 is the node ID. you will have to ensure that you are accessing node names while writing the query.

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
       'was implemented in', 'ended in', 'established first factory in',
       'gained Diwani rights in', 'happened in', 'arrived in India in',
       'was reversed in', 'was founded during', 'started during',
       'was introduced by', 'was dominated by', 'was reorganized by',
       'was established by']

    Here are the head node names: 

    ['Maharashtra', 'Mumbai', 'Karnataka', 'Bengaluru', 'TamilNadu',
       'Chennai', 'Kerala', 'Thiruvananthapuram', 'AndhraPradesh',
       'Hyderabad', 'UttarPradesh', 'Lucknow', 'Bihar', 'Patna',
       'WestBengal', 'Kolkata', 'Gujarat', 'Gandhinagar', 'Rajasthan',
       'Jaipur', 'MadhyaPradesh', 'Bhopal', 'Punjab', 'Chandigarh',
       'Haryana', 'Odisha', 'Bhubaneswar', 'Assam', 'Dispur', 'Jharkhand',
       'Ranchi', 'Chhattisgarh', 'Raipur', 'Uttarakhand', 'Dehradun',
       'HimachalPradesh', 'Shimla', 'Goa', 'Panaji', 'Tamil', 'Odia',
       'Hindi', 'Telugu', 'Kannada', 'Bengali', 'Punjabi', 'Ganges',
       'Yamuna', 'Brahmaputra', 'Godavari', 'Krishna', 'Narmada', 'Tapi',
       'Mahanadi', 'Kaveri', 'Indus', 'Himalayas', 'WesternGhats',
       'EasternGhats', 'AravalliRange', 'VindhyaRange', 'SatpuraRange',
       'NilgiriHills', 'ShivalikHills', 'Diwali', 'Holi', 'Eid',
       'Christmas', 'GaneshChaturthi', 'DurgaPuja', 'Onam', 'Pongal',
       'Baisakhi', 'Navratri', 'India', 'Pakistan', 'China', 'Nepal',
       'Bhutan', 'Bangladesh', 'Myanmar', 'SriLanka', 'Maldives',
       'TajMahal', 'RedFort', 'QutubMinar', 'GatewayOfIndia', 'HawaMahal',
       'VictoriaMemorial', 'Charminar', 'GoldenTemple',
       'BalGangadharTilak', 'LataMangeshkar', 'SachinTendulkar',
       'RabindranathTagore', 'SatyajitRay', 'SouravGanguly',
       'MSSubbulakshmi', 'ARRahman', 'ViswanathanAnand', 'MahatmaGandhi',
       'SardarPatel', 'NarendraModi', 'AmitabhBachchan',
       'JawaharlalNehru', 'KalpanaChawla', 'APJAbdulKalam', 'Mammootty',
       'ShashiTharoor', 'BhagatSingh', 'DiljitDosanjh', 'KapilDev',
       'Mirabai', 'PrithvirajChauhan', 'RaniPadmini', 'VadaPav',
       'PavBhaji', 'PuranPoli', 'Rasgulla', 'MacherJhol', 'MishtiDoi',
       'Dosa', 'Idli', 'Dhokla', 'Thepla', 'Khandvi', 'Kebabs', 'Biryani',
       'Jalebi', 'Appam', 'Puttu', 'KarimeenPollichathu', 'MakkiDiRoti',
       'SarsonDaSaag', 'ButterChicken', 'DalBaatiChurma', 'Ghewar',
       'LaalMaas', 'Lavani', 'Koli', 'Kathak', 'GaudiyaNritya',
       'Bharatanatyam', 'Karakattam', 'Garba', 'Dandiya', 'Raslila',
       'Kathakali', 'Mohiniyattam', 'Bhangra', 'Giddha', 'Ghoomar',
       'Kalbelia', 'FatehpurSikri', 'Delhi', 'AmberFort', 'AjantaCaves',
       'BrihadeeswararTemple', 'MeenakshiTemple', 'KonarkSunTemple',
       'JagannathTemple', 'Hampi', 'MysorePalace', 'RaniKiVav',
       'SomnathTemple', 'IndianIndependence', 'GopalKrishnaGokhale',
       'VinayakDamodarSavarkar', 'SubhashChandraBose', 'KhudiramBose',
       'RashBehariBose', 'SardarVallabhbhaiPatel', 'DadabhaiNaoroji',
       'ChandraShekharAzad', 'RaniLakshmibai', 'JayaprakashNarayan',
       'RajendraPrasad', 'AnugrahNarayanSinha', 'LalaLajpatRai',
       'UdhamSingh', 'SubramaniaBharati', 'VOChidambaramPillai',
       'CRajagopalachari', 'KKelappan', 'AKGopalan', 'VakkomMoulavi',
       'AlluriSitaramaRaju', 'TanguturiPrakasam', 'PottiSreeramulu',
       'GopabandhuDas', 'BijuPatnaik', 'UtkalGouravMadhusudanDas',
       'NonCooperationMovement', 'N1920', 'Ahmedabad',
       'QuitIndiaMovement', 'N1942', 'SwadeshiMovement', 'N1905',
       'CivilDisobedienceMovement', 'N1930', 'Sabarmati',
       'ChamparanSatyagraha', 'N1917', 'Champaran', 'KhedaSatyagraha',
       'N1918', 'Kheda', 'SaltMarch', 'Dandi', 'KakoriConspiracy',
       'N1925', 'RamPrasadBismil', 'Kakori', 'JallianwalaBaghMassacre',
       'N1919', 'GeneralDyer', 'Amritsar', 'ChauriChauraIncident',
       'N1922', 'ChauriChaura', 'SabarmatiAshram', 'JallianwalaBagh',
       'IndianNationalArmy', 'N1945', 'CellularJail', 'AndamanAndNicobar',
       'FreedomFighters', 'N1906', 'AgaKhanPalace', 'BritishRaj', 'N1921',
       'N1924', 'IndiaGate', 'N1931', 'WarrenHastings',
       'GovernorsGeneral', 'N1773', 'FirstGovernorGeneral', 'Calcutta',
       'LordCornwallis', 'N1786', 'PermanentSettlement', 'LordWellesley',
       'N1798', 'SubsidiaryAlliance', 'LordWilliamBentinck', 'N1828',
       'AbolitionOfSati', 'LordDalhousie', 'N1848', 'DoctrineOfLapse',
       'LordCanning', 'N1856', 'FirstViceroy', 'LordCurzon', 'N1899',
       'PartitionOfBengal', 'LordMountbatten', 'N1947', 'LastViceroy',
       'NewDelhi', 'RobertClive', 'MilitaryOfficers', 'N1757',
       'BattleOfPlassey', 'Bengal', 'JamesOutram', 'N1857',
       'IndianRebellion', 'LordKitchener', 'N1902', 'ArmyReforms',
       'ThomasMacaulay', 'Administrators', 'N1834', 'EnglishEducation',
       'CharlesWood', 'N1854', 'WoodSDispatch', 'London', 'JohnLawrence',
       'N1864', 'PunjabAdministration', 'Lahore', 'WilliamSleeman',
       'N1830', 'ThuggeeSuppression', 'CentralIndia', 'EastIndiaCompany',
       'N1600', 'TradingCompany', 'IndianCivilService', 'N1858',
       'AdministrativeService', 'IndianPoliceService', 'N1861',
       'PoliceForce', 'IndianArmy', 'MilitaryForce', 'PresidencyColleges',
       'N1817', 'Education', 'RailwaySystem', 'N1853', 'Transportation',
       'Bombay', 'TelegraphSystem', 'N1851', 'Communication',
       'PostalSystem', 'N1793', 'LandRevenue', 'AnnexationPolicy',
       'MilitaryPolicy', 'DivideAndRule', 'PoliticalPolicy', 'IlbertBill',
       'N1883', 'JudicialReform', 'RowlattAct', 'RepressiveLaw',
       'GovernmentOfIndiaAct', 'ConstitutionalReform',
       'IndianCouncilsAct', 'LegislativeReform', 'Surat', 'N1765',
       'BattleOfBuxar', 'N1764', 'FirstWarOfIndependence',
       'SimonCommission', 'N1928', 'CrippsMission', 'CabinetMission',
       'N1946', 'N1911', 'IndianNationalCongress', 'BritishRule',
       'MuslimLeague', 'IndianRailways', 'IndianPostalService', 'British',
       'IndianPolice']]    
       
    """
    result = chain.invoke(final_query)

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
    app = create_react_agent(llm, tools)
    final_state = app.invoke({"messages": [{"role": "user", "content": query}]})
    return final_state["messages"][-1].content
    