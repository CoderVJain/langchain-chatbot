from langgraph.graph import StateGraph, START
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages
from dotenv import load_dotenv


load_dotenv()

model  = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

class State(TypedDict):

  messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: State):

  messages = state['messages']
  response = model.invoke(messages);
  return {'messages' : [response]}

checkpointer = InMemorySaver()

graph = StateGraph(State)
graph.add_node('chat_node',chat_node)
graph.add_edge(START,'chat_node')
chatbot = graph.compile(checkpointer=checkpointer)


