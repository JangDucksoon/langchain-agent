import os
from langchain_core.messages import AIMessage, HumanMessage

class CommandManager:
    @staticmethod
    def clear_console():
        os.system("cls" if os.name == "nt" else "clear")

    @staticmethod
    async def show_history(history_mode, history_object):
        if history_mode == "M":
            session_id = history_object["session_id"]
            store = history_object["store"]

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
        elif history_mode == "D":
            sql_history = history_object["sql_history"]
            messages = await sql_history.aget_messages()
            if len(messages) > 0:
                print(f"{'---' * 30} History {'---' * 30} ")

                for type in messages:
                    if isinstance(type, HumanMessage):
                        print(f"Question :: {type.content}")
                    elif isinstance(type, AIMessage):
                        print(f"Answer > {type.content}")

                print(f"{'---' * 30} History End {'---' * 30} ")
            else:
                print(f"{'---' * 30} No History {'---' * 30} ")