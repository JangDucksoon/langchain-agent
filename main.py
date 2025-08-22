from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_tavily import TavilySearch
from langchain.agents import create_react_agent, AgentExecutor
from util.util import pretty_event_print
from command.command import CommandManager

# model select
llm = ChatOllama(model="llama3.1:8b-instruct-q4_K_M", temperature=0.2)
prompt = ChatPromptTemplate.from_messages([
    ("system", """
        You have access to the following tools:
        {tools}
        DO NOT translate or change these markers or tool names:
        - Thought:
        - Action:
        - Action Input:
        - Observation:
        - Final Answer:

        Rules:
        1. If the input is trivial (e.g. greeting, small talk, obvious knowledge), 
        DO NOT use any Action. Go directly to:
        Final Answer: <your answer in {language}>

        2. If you can answer the input without using any tool, 
        DO NOT use any Action. Go directly to:
        Final Answer: <your answer in {language}>

        3. Only if the input cannot be answered without a tool, 
        then follow the standard ReAct format:
        Thought:
        Action: <tool name from {tool_names}>
        Action Input: "<plain text input>"
        Observation: <result>
        (repeat as needed)

        4. You must ALWAYS end with exactly one:
        Final Answer: <your answer in {language}>
    """),
    ("human", "{input}\n{agent_scratchpad}")
])
parser = StrOutputParser()

#tool
search_tool = TavilySearch(max_results=3, tavily_api_key="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")
tools = [search_tool]

agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
agent_exec = AgentExecutor(agent=agent, tools=tools, verbose=False, handle_parsing_errors=True)

#프롬프트 체인
chain = prompt | llm | parser

#language
prompt_language = "Korean"
print(f"[Language :: {prompt_language}]\n{'-' * 60}\n")

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

    for event in agent_exec.stream({"input": user_input, "language": prompt_language}):
        pretty_event_print(event)
    print()