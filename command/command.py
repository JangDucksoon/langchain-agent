import os
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.chat_history import InMemoryChatMessageHistory

class CommandManager:
    @staticmethod
    def clear_console():
        os.system("cls" if os.name == "nt" else "clear")

    @staticmethod
    def show_history(session_id, store):
        if session_id in store and len(store[session_id].messages) > 0:
            print(f"{'---' * 30} History {'---' * 30} ")

            for type in store[session_id].messages:
                if isinstance(type, HumanMessage):
                    print(f"Question :: {type.content}")
                elif isinstance(type, AIMessage):
                    print(f"Answer > {type.content}")

            print(f"{'---' * 30} History End {'---' * 30} ")
        else:
            print(f"{'---' * 30} No History {'---' * 30} ")