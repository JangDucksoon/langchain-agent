import uuid
from fastapi import FastAPI
from fast_api.chat_request import ChatRequest
from fastapi.responses import StreamingResponse
from util.util import pretty_event_print_api
from contextlib import asynccontextmanager
from pydantic  import BaseModel
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_tavily import TavilySearch
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.chat_history import InMemoryChatMessageHistory
from sqlalchemy.ext.asyncio import create_async_engine
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import SQLChatMessageHistory
from mcp_server.mcpManager import McpManager
from callback.loggingCallbackHandler import LoggingCallbackHandler
from tools.time import get_current_time_by_country
from tools.fileSystem import find_files_in_directory, read_file, write_file, delete_file
from tools.codeExecuter import execute_python_code, execute_python_docker
from util.util import pretty_event_print
from util.history_message_converter import HistoryMessageConverter
from command.command import CommandManager
from checking_ollama import check_ollama_serving

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
                5. If a user sends a request related to the MCP server, consider using the MCP server tool first rather than the python code execution tool.
                   ***
                    Example: Insert data into Test table, please -> Use Execute DB tools, not execute_python_docker, execute_python_code
                   ***
                6. Never call any tools more than once with same request (if there are different values of variables, you can call more)
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
                7. When using tavily_search or search_web tool:
                    - FIRST, you must call get_current_time_by_country tool to know today's date
                    - Use this current date information to make your search query more specific and relevant
                    - NEVER use time_range variable when calling tool
                    - You must not call it more than once per question
                    - Always request up to 5 results in a single call and make the answer from those results.
                8. When user request
    """),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

#tool
search_tool = TavilySearch(max_results=5, tavily_api_key="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")
tools = [ search_tool, get_current_time_by_country, find_files_in_directory, read_file, write_file, delete_file, execute_python_code, execute_python_docker ]

#mcp servers
#mcp_servers = McpManager("mcp_config.json")
#tools.extend(mcp_servers.get_tools()) -> fast api initialize에서 이동

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
    #db에 utf-8 문자를 저장하기 위해 커스텀 클래스 구현
    return SQLChatMessageHistory(
        session_id = session_id,
        connection = engine,
        custom_message_converter=HistoryMessageConverter("message_store")
    )
history_mode = "D" # M: memory -> get_session_history, D: database -> get_session_history_db

#language
prompt_language = "Korean"
print(f"[Language :: {prompt_language}]\n{'-' * 60}")

#custom properties
show_think = True
SESSION_ID = str(uuid.uuid4())
print(f"[SESSION_ID :: {SESSION_ID}]\n{'-' * 60}")

print(f"[History mode :: {"Database" if history_mode == "D" else "Memory"}]\n{'-' * 60}\n")

#life span conetxt manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    check_ollama_serving()      #ollama run check

    # model select
    llm = ChatOllama(model="gpt-oss:20b", temperature=0.2)

    #mcp server
    mcp_servers = McpManager("mcp_config.json")

    #agent
    agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
    agent_exec = AgentExecutor(agent=agent, tools=tools, callbacks=callbacks, verbose=False)

    agent_with_history = RunnableWithMessageHistory(
        runnable=agent_exec,
        get_session_history=get_session_history_db,
        input_messages_key="input",
        history_messages_key="chat_history",
    )

    await mcp_servers._McpManager__initialize()
    tools.extend(mcp_servers.get_tools())
    app.state.agent_with_history = agent_with_history

    yield
    print("shuting down...")

#fast api 라우터
app = FastAPI(lifespan=lifespan)

@app.post("/chat")
async def chat(request: ChatRequest):
    session_id = request.session_id or SESSION_ID if history_mode == "M" else "jds"

    result = await app.state.agent_with_history.ainvoke(
        {"input": request.message, "language": prompt_language}, config={"configurable": {"session_id": session_id}}
    )

    return {"output": result["output"]}

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    session_id = request.session_id or SESSION_ID if history_mode == "M" else "jds"

    async def event_generator():
        async for event in app.state.agent_with_history.astream({"input": request.message, "language": prompt_language}, config={"configurable": {"session_id": session_id}}):
            for msg in pretty_event_print_api(event):
                yield msg

    return StreamingResponse(event_generator(), media_type="text/plain")