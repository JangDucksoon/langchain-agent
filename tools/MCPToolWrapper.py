from langchain_core.tools import BaseTool
from typing import Type, Any


class MCPToolWrapper(BaseTool):
    name: str
    description: str
    original_tool: Any
    server_name: str
    mcp_client: Any

    def __init__(self, original_tool, server_name: str, mcp_client, **kwargs):
        new_name = f"{server_name}_{original_tool.name}"
        new_description = f"[{server_name}] {original_tool.description}"

        super().__init__(
            name=new_name,
            description=new_description,
            original_tool=original_tool,
            server_name=server_name,
            mcp_client=mcp_client
        )

    def _run(self, *args, **kwargs) -> str:
        return self.mcp_client.call_tool(
            server_name=self.server_name,
            tool_name=self.original_tool.name,
            arguments=kwargs
        )
    
    async def _arun(self, *args, **kwargs) -> str:
          return await self.mcp_client.acall_tool(
              server_name=self.server_name,
              tool_name=self.original_tool.name,
              arguments=kwargs
          )