import os
import json
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient

EMPTY_MCP_SERVER_CONFIG = {"mcpServers": {}}

class McpManager:
    def __init__(self, config_file="mcp_config.json"):
        self.config_path = os.path.join(os.path.dirname(__file__), "..", config_file)

        self.client = None
        self.mcp_server_list = None
        self.tools = []
        self.is_initialized = False

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
            self.tools = await self.client.get_tools()
            self.is_initialized = True

            self.mcp_server_list = list(config["mcpServers"].keys())
            print(f"MCP Server list : {self.mcp_server_list}")
            print(f"MCP initialized ! : {[tool.name for tool in self.tools]}\n")
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