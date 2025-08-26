import uuid
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_tavily import TavilySearch
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from callback.loggingCallbackHandler import LoggingCallbackHandler
from tools.time import get_current_time_by_country
from tools.fileSystem import find_files_in_directory, read_file, write_file, delete_file
from util.util import pretty_event_print
from command.command import CommandManager

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
tools = [ search_tool, get_current_time_by_country, find_files_in_directory, read_file, write_file, delete_file ]

#callback
logging_callback = LoggingCallbackHandler()
callbacks = [ logging_callback ]

#memory for chat history
store = {}
def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

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
print(f"[Language :: {prompt_language}]\n{'-' * 60}\n")

#custom properties
show_think = True
SESSION_ID = str(uuid.uuid4())
print(f"[SESSION_ID :: {SESSION_ID}]\n{'-' * 60}\n")

while True:
    user_input = input("Question :: ")


    if user_input.lower() in ["/exit", "exit"]:
        break

    if user_input.lower() in ["/clear", "clear"]:
        CommandManager.clear_console()
        continue

    if user_input.lower() in ["/history", "history"]:
        CommandManager.show_history(SESSION_ID, store)
        continue

    if user_input.lower() in ["/reset", "reset"]:
        if SESSION_ID in store:
            store[SESSION_ID].clear()
        print("----------------------------Memory reset--------------------")
        continue

    if user_input.lower().startswith("/lang"):
        if len(user_input.split(" ")) == 2:
            prompt_language = user_input.split(" ")[1]
        print(f"prompt language :: {prompt_language}")
        continue

    if user_input.lower().startswith('/think'):
        if len(user_input.split(" ")) == 2:
            value = user_input.split(" ")[1]
            if value in ("True", "False"):
                show_think = True if value == "True" else False if value == "False" else show_think
            else:
                print("You should enter True or False")
        print(f"current mode :: show think > {show_think}")
        continue

    if show_think:
        for event in agent_with_history.stream({"input": user_input, "language": prompt_language}, config={"configurable": {"session_id": SESSION_ID}}):
            pretty_event_print(event)
    else:
        response = agent_with_history.invoke({"input": user_input, "language": prompt_language}, config={"configurable": {"session_id": SESSION_ID}})
        print(f"answer > {response['output']}")

    print()