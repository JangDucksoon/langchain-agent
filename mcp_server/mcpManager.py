import os
import sys
import json
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import StructuredTool, BaseTool
from typing import Any

EMPTY_MCP_SERVER_CONFIG = {"mcpServers": {}}

class McpManager:
    def __init__(self, config_file="mcp_config.json"):
        self.config_path = os.path.join(os.path.dirname(__file__), "..", config_file)

        self.client = None
        self.mcp_server_list = None
        self.tools = []
        self.is_initialized = False

        filename = os.path.basename(sys.argv[0])
        if filename == "main.py":
            asyncio.run(self.__initialize())

    def __load_config(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            print("Can not find mcp server config file")
            return EMPTY_MCP_SERVER_CONFIG
        except Exception as e:
            print(f"An occurred Error : {e}")
            return EMPTY_MCP_SERVER_CONFIG

    async def __initialize(self):
        try:
            config = self.__load_config()
            self.client = MultiServerMCPClient(config["mcpServers"])
            self.mcp_server_list = list(config["mcpServers"].keys())
            self.tools = []

            #서버별 tool 구분 (동일한 mcp 모듈의 target server 가 다른경우 고려)
            for server_name in self.mcp_server_list:
                """ self.tools = await self.client.get_tools(server_name=server_name) """
                server_tools = await self.client.get_tools(server_name=server_name)
                for tool in server_tools:
                    self.tools.append(self.__make_alias_tool(server_name, tool))
            print(f"MCP Server list : {self.mcp_server_list}")
            print(f"MCP initialized ! : {[tool.name for tool in self.tools]}\n")
            self.is_initialized = True
            return True
        except Exception as e:
            print(f"MCP initialize Error : {e}")
            return False

    def get_tools(self):
        if not self.is_initialized:
            print("MCP Server is not initialized yet")
            return []
        return self.tools

    def get_mcp_server_list(self):
        return self.mcp_server_list

    def __make_alias_tool(self, server_label: str, base_tool: BaseTool) -> StructuredTool:
        """wrapper tool 반환 (동일한 mcp 모듈에 target 서버가 다른경우 충돌을 막기 위함)"""
        new_name = f"{server_label}_{base_tool.name}"
        new_description=f"[{server_label}] {base_tool.description}"
        original = base_tool
        args_schema = getattr(original, "args_schema", None)

        #동기 호출
        def _sync(**kwargs: Any):
            return original.invoke(kwargs)

        #비동기 호출
        async def _async(**kwargs: Any):
            return await original.ainvoke(kwargs)

        return StructuredTool.from_function(
            name=new_name,
            description=new_description,
            args_schema=args_schema,
            func=_sync,
            coroutine=_async
        )

