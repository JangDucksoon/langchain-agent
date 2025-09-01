import uuid
import asyncio
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_tavily import TavilySearch
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.chat_history import InMemoryChatMessageHistory
from sqlalchemy.ext.asyncio import create_async_engine
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from mcp_server.mcpManager import McpManager
from callback.loggingCallbackHandler import LoggingCallbackHandler
from tools.time import get_current_time_by_country
from tools.fileSystem import find_files_in_directory, read_file, write_file, delete_file
from tools.codeExecuter import execute_python_code, execute_python_docker
from util.util import pretty_event_print
from command.command import CommandManager
from checking_ollama import check_ollama_serving

check_ollama_serving()

# model select
llm = ChatOllama(model="gpt-oss:20b", temperature=0.2)

#tool calling prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", """
                You are a helpful AI assistant that can use tools to answer questions. Answer in {language}.

                Guidelines:
                1. For simple questions you can answer with your knowledge, respond directly in natural language without using tools.
                2. If a tool is needed, respond with the correct function call in JSON format as defined by the system (do not mix text and JSON).
                3. After receiving a tool result, always give the final answer in natural language, not JSON.
                4. !!!CRITICAL!!!: Before calling any tool, check the "agent_scratchpad" section above.
                    Look for previous "Action:" and "Action Input:" entries.
                    If you see the SAME tool with SAME input already executed, DO NOT call it again.

                    Example: If agent_scratchpad shows:
                    "Action: get_current_time_by_country
                        Action Input: {{'timezone': 'Europe/Moscow'}}
                        Observation: 2025-08-26 08:46:36"
                    Then DO NOT call get_current_time_by_country with timezone='Europe/Moscow' again!
                5. Never call any tools more than once with same request (if there are different values of variables, you can call more)
                    STEP-BY-STEP CHECK before each tool call:
                    Step 1: Look at your action history above
                    Step 2: Check if you already called this exact tool with these exact parameters
                    Step 3: If YES → STOP, use the previous result
                    Step 4: If NO → Proceed with the tool call

                    ***
                    Example of GOOD tool usage:
                    Case1) get_time() → tavily_search() → write_file() (different tools)
                    Case2) get_time(timezone='Asia/Seoul') → get_time(timezone='America/New_York') (same tool, different params)

                    Example of BAD tool usage:
                    Case1) tavily_search(query='Apple') → tavily_search(query='Apple') (exact duplicate)
                    ***
                6. When using tavily_search or search_web tool:
                    - FIRST, you must call get_current_time_by_country tool to know today's date
                    - Use this current date information to make your search query more specific and relevant
                    - NEVER use time_range variable when calling tool
                    - You must not call it more than once per question
                    - Always request up to 5 results in a single call and make the answer from those results.
    """),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

#tool
search_tool = TavilySearch(max_results=5, tavily_api_key="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")
tools = [ search_tool, get_current_time_by_country, find_files_in_directory, read_file, write_file, delete_file, execute_python_code, execute_python_docker ]

#mcp servers
mcp_servers = McpManager("mcp_config.json")
tools.extend(mcp_servers.get_tools())

#callback
logging_callback = LoggingCallbackHandler()
callbacks = [ logging_callback ]

#memory for chat history
store = {} #History Cache
def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

#sqllist for chat history
engine = create_async_engine("sqlite+aiosqlite:///chat_history.db") #async io for db
def get_session_history_db(session_id:str):
    return SQLChatMessageHistory(
        session_id = session_id,
        connection = engine
    )
history_mode = "M" # M: memory -> get_session_history, D: database -> get_session_history_db

#agent
agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
agent_exec = AgentExecutor(agent=agent, tools=tools, callbacks=callbacks, verbose=False)

agent_with_history = RunnableWithMessageHistory(
    runnable=agent_exec,
    get_session_history=get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
)

#language
prompt_language = "Korean"
print(f"[Language :: {prompt_language}]\n{'-' * 60}")

#custom properties
show_think = True
SESSION_ID = str(uuid.uuid4())
print(f"[SESSION_ID :: {SESSION_ID}]\n{'-' * 60}")

print(f"[History mode :: {"Database" if history_mode == "D" else "Memory"}]\n{'-' * 60}\n")

async def main():
    global show_think, prompt_language, history_mode
    while True:
        print(f"{'===' * 30}")
        user_input = input("Question :: ")

        ############## Command Area #######################
        if user_input.lower() in ["/exit", "exit"]:
            break

        if user_input.lower() in ["/clear", "clear"]:
            CommandManager.clear_console()
            continue

        if user_input.lower() in ["/history", "history"]:
            history_object = {"session_id": SESSION_ID, "store": store} if history_mode == "M" else {"sql_history": get_session_history_db(user_name)}
            await CommandManager.show_history(
                history_mode=history_mode,
                history_object=history_object
            )
            continue

        if user_input.lower() in ["/change-history-mode", "change history mode"]:
            history_mode = "D" if history_mode == "M" else "M"

            if history_mode == "D":
                agent_with_history.get_session_history = get_session_history_db
                user_name = input("set your name > ")
                if not user_name:
                    history_mode = "M"
                    agent_with_history.get_session_history = get_session_history
                    print("If you don't set your name, can not use database for chat history store")
                else:
                    print(f"Hellow {user_name} !!")
            else:
                agent_with_history.get_session_history = get_session_history

            print(f"Current history mode > {"Database" if history_mode == "D" else "Memory"}")
            continue

        if user_input.lower() in ["/reset", "reset"]:
            if history_mode == "M":
                if SESSION_ID in store:
                    store[SESSION_ID].clear()
                print("----------------------------Memory reset--------------------")
            elif history_mode == "D":
                if user_name:
                    await get_session_history_db(user_name).aclear()
                else:
                    print(f"--------------------{user_name}'s history reset in DB----------------------")
                    print("----------------------------history reset in DB--------------------")
            continue

        if user_input.lower().startswith("/lang"):
            if len(user_input.split(" ")) == 2:
                prompt_language = user_input.split(" ")[1]
            print(f"prompt language :: {prompt_language}")
            continue

        if user_input.lower().startswith("/think"):
            if len(user_input.split(" ")) == 2:
                value = user_input.split(" ")[1]
                if value in ("True", "False"):
                    show_think = True if value == "True" else False if value == "False" else show_think
                else:
                    print("You should enter True or False")
            print(f"current mode :: show think > {show_think}")
            continue

        if user_input.lower().startswith("/tools"):
            print("[tools]")
            print([tool.name for tool in tools])
            continue

        if user_input.lower().startswith("/mcps"):
            print("[mcps]")
            print(mcp_servers.get_mcp_server_list())
            continue

        if user_input.lower() in ["/info", "info"]:
            print(f"\n[Language :: {prompt_language}]\n{'-' * 60}")
            print(f"[SESSION_ID :: {SESSION_ID}]\n{'-' * 60}")
            print(f"[History mode :: {"Database" if history_mode == "D" else "Memory"}]\n{'-' * 60}\n")
            continue

        if user_input.strip() == "":
            continue

        ############## Command Area #######################
        if show_think:
            async for event in agent_with_history.astream({"input": user_input, "language": prompt_language}, config={"configurable": {"session_id": SESSION_ID if history_mode == "M" else user_name}}):
                pretty_event_print(event)
        else:
            response = await agent_with_history.ainvoke({"input": user_input, "language": prompt_language}, config={"configurable": {"session_id": SESSION_ID if history_mode == "M" else user_name}})
            print(f"answer > {response['output']}")

        print(f"{'===' * 30}\n")

if __name__ == "__main__":
    asyncio.run(main())