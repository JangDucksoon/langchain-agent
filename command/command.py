import os
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langchain_core.chat_history import InMemoryChatMessageHistory

class CommandManager:
    @staticmethod
    def clear_console():
        os.system("cls" if os.name == "nt" else "clear")