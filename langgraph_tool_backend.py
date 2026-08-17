from langgraph.graph import StateGraph, START
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import sqlite3
import requests
import os


load_dotenv()

model  = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# Tools 

search_tool = DuckDuckGoSearchRun(region="us-en")

@tool
def calculator(first_num : float, second_num : float, operation : str) -> dict:
    """
    Perform a basic arithmetic operation on two numbers.
    Supported operations are: add, subtract, multiply, divide.
    """
    try:
        if operation == "add":
            result= first_num + second_num
        elif operation == "subtract":
            result = first_num - second_num
        elif operation == "multiply":
            result = first_num * second_num
        elif operation == "divide":
            if second_num == 0:
                return {"error": "Division by zero is not allowed."}
            result = first_num / second_num
        else:
            return {"error": f"Unsupported operation: {operation}. Supported operations are: add, subtract, multiply, divide."}

        return {"first_number": first_num, "second_number": second_num, "operation" : operation,"result": result}
    except Exception as e:
        return {"error": str(e)}

@tool
def get_stock_price(symbol: str) -> dict:
    """
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={os.getenv('ALPHA_VANTAGE_API_KEY')}"
    r = requests.get(url)
    return r.json()

tools = [search_tool, calculator, get_stock_price]

llm_with_tools = model.bind_tools(tools)


class State(TypedDict):
  messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: State):
  """LLM node that may answer or request a tool call"""  
  messages = state['messages']
  response = llm_with_tools.invoke(messages);
  return {'messages' : [response]}

tool_node = ToolNode(tools)

conn = sqlite3.connect('chatbot.db', check_same_thread=False)

checkpointer = SqliteSaver(conn=conn)

graph = StateGraph(State)
graph.add_node('chat_node',chat_node)
graph.add_node('tools',tool_node)

graph.add_edge(START,'chat_node')
graph.add_conditional_edges('chat_node', tools_condition)
graph.add_edge('tools','chat_node')

chatbot = graph.compile(checkpointer=checkpointer)


def get_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])
    
    return list(all_threads)