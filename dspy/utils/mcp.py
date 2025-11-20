from typing import TYPE_CHECKING, Any

from dspy.adapters.types.tool import Tool, convert_input_schema_to_tool_args

if TYPE_CHECKING:
    import mcp


def _convert_mcp_tool_result(call_tool_result: "mcp.types.CallToolResult") -> str | list[Any] | dict[str, Any]:
    """Convert MCP tool result to DSPy-compatible format.
    
    Prefers structured content if available, otherwise falls back to text content.
    """
    from mcp.types import TextContent

    if call_tool_result.isError:
        text_contents: list[TextContent] = []
        for content in call_tool_result.content:
            if isinstance(content, TextContent):
                text_contents.append(content.text)
        error_msg = " ".join(text_contents) if text_contents else "Unknown error"
        raise RuntimeError(f"Failed to call MCP tool: {error_msg}")

    # Prefer structured content if available
    if call_tool_result.structuredContent is not None:
        return call_tool_result.structuredContent
    
    # Fall back to text content if no structured content
    text_contents: list[TextContent] = []
    non_text_contents = []
    for content in call_tool_result.content:
        if isinstance(content, TextContent):
            text_contents.append(content)
        else:
            non_text_contents.append(content)

    tool_content = [content.text for content in text_contents]
    if len(text_contents) == 1:
        tool_content = tool_content[0]

    return tool_content or non_text_contents


def convert_mcp_tool(session: "mcp.ClientSession", tool: "mcp.types.Tool") -> Tool:
    """Build a DSPy tool from an MCP tool.

    Args:
        session: The MCP session to use.
        tool: The MCP tool to convert.

    Returns:
        A dspy Tool object.
    """
    args, arg_types, arg_desc = convert_input_schema_to_tool_args(tool.inputSchema)

    # Convert the MCP tool and Session to a single async method
    async def func(*args, **kwargs):
        result = await session.call_tool(tool.name, arguments=kwargs)
        return _convert_mcp_tool_result(result)

    return Tool(
        func=func,
        name=tool.name,
        desc=tool.description,
        args=args,
        arg_types=arg_types,
        arg_desc=arg_desc,
        output_schema=tool.outputSchema,
    )
