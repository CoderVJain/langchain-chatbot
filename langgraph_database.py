from langgraph.graph import StateGraph, START
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import sqlite3

load_dotenv()

model  = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

class State(TypedDict):

  messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: State):

  messages = state['messages']
  response = model.invoke(messages);
  return {'messages' : [response]}

conn = sqlite3.connect('chatbot.db', check_same_thread=False)

checkpointer = SqliteSaver(conn=conn)

graph = StateGraph(State)
graph.add_node('chat_node',chat_node)
graph.add_edge(START,'chat_node')
chatbot = graph.compile(checkpointer=checkpointer)


def get_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])
    
    return list(all_threads)