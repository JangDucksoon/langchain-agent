from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_tavily import TavilySearch
from langchain.agents import AgentExecutor, create_tool_calling_agent
from callback.loggingCallbackHandler import LoggingCallbackHandler
from tools.time import get_current_time_by_country
from tools.fileSystem import find_files_in_directory, read_file, write_file
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
                4. Be efficient – avoid calling the same tool multiple times with identical parameters.
                5. When using tavily_search or search_web tool:
                   - FIRST, you must call get_current_time_by_country tool to know today's date
                   - Use this current date information to make your search query more specific and relevant
                   - NEVER use time_range variable when calling tool
                   - You must not call it more than once per question
                   - Always request up to 5 results in a single call and make the answer from those results.
    """),
    ("placeholder", "{agent_scratchpad}"),
    ("human", "{input}")
])

#tool
search_tool = TavilySearch(max_results=5, tavily_api_key="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")
tools = [ search_tool, get_current_time_by_country, find_files_in_directory, read_file, write_file ]

#callback
logging_callback = LoggingCallbackHandler()
callbacks = [ logging_callback ]

agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
agent_exec = AgentExecutor(agent=agent, tools=tools, verbose=False, handle_parsing_errors=True, callbacks=callbacks)

#language
prompt_language = "Korean"
print(f"[Language :: {prompt_language}]\n{'-' * 60}\n")

show_think = True

while True:
    user_input = input("Question :: ")


    if user_input.lower() in ["/exit", "exit"]:
        break

    if user_input.lower() in ["/clear", "clear"]:
        CommandManager.clear_console()
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
        for event in agent_exec.stream({"input": user_input, "language": prompt_language}):
            pretty_event_print(event)
    else:
        response = agent_exec.invoke({"input": user_input, "language": prompt_language})
        print(f"answer > {response['output']}")
    
    print()