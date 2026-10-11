"""
==============================================================================
V12 - PERSONAL AGENT BUILDER: TOOL REGISTRY MODULE
==============================================================================
Concept & Architecture:
This module provides the extensible Tool System for the Personal Agent Builder.
In Agentic AI, tools represent the actuators through which an LLM interacts with
the outside world (file systems, calculations, APIs, databases).

Key Features:
1. `Tool` Model: Represents a callable tool with typed parameter specifications,
   educational docstrings, and explicit `risk_level` tagging ("SAFE", "MODERATE", "DANGEROUS").
2. `ToolRegistry`: A pluggable catalog where agents register only the tools they need.
3. JSON Schema Generation: Automatically produces OpenAI/Ollama compatible tool definitions
   for prompt engineering.
4. Safe Execution: Catches execution errors gracefully without terminating the agent session.
==============================================================================
"""

# Import standard library modules for system inspection and execution
import os
import ast
import operator
import inspect
from typing import Callable, Dict, Any, List, Optional


# ==============================================================================
# SECTION 1: TOOL DEFINITION DATA STRUCTURE
# ==============================================================================

class Tool:
    """
    Represents an actionable tool that can be invoked by a Personal Agent.

    Attributes:
    -----------
    name : str
        The unique identifier of the tool (e.g., 'create_file').
    description : str
        Human/LLM-readable description explaining the tool's purpose and usage.
    func : Callable
        The underlying Python function to invoke when the tool is called.
    risk_level : str
        Safety classification: 'SAFE' (read-only), 'MODERATE' (state change),
        or 'DANGEROUS' (destructive/code execution).
    parameters : dict
        Mapping of parameter names to their descriptions and types.
    """

    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        risk_level: str = "SAFE",
        parameters: Optional[Dict[str, str]] = None
    ):
        self.name = name
        self.description = description
        self.func = func
        self.risk_level = risk_level.upper()
        self.parameters = parameters or {}

    def execute(self, **kwargs) -> Any:
        """
        Executes the wrapped Python callable with provided keyword arguments.

        Parameters:
        -----------
        **kwargs : dict
            Keyword arguments passed from the LLM tool call payload.

        Returns:
        --------
        Any : Return value of the tool function, or formatted error string on failure.
        """
        try:
            return self.func(**kwargs)
        except Exception as error:
            return f"Error executing tool '{self.name}': {str(error)}"

    def to_schema_prompt(self) -> str:
        """
        Formats the tool specification into a human and LLM-friendly schema prompt.

        Returns:
        --------
        str : Text block describing tool name, risk, parameters, and purpose.
        """
        params_str = ", ".join([f"{k}: {v}" for k, v in self.parameters.items()])
        return f"- {self.name}({params_str}) [Risk: {self.risk_level}]: {self.description}"


# ==============================================================================
# SECTION 2: PLUGGABLE TOOL REGISTRY
# ==============================================================================

class ToolRegistry:
    """
    A dynamic container managing tools available to a specific Personal Agent instance.
    Agents can register any arbitrary Python function as an actuator.
    """

    def __init__(self):
        """Initializes an empty registry dictionary."""
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """
        Registers a new Tool instance in the catalog.

        Parameters:
        -----------
        tool : Tool
            The tool to add to the registry.
        """
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """
        Retrieves a registered Tool by its unique name.

        Parameters:
        -----------
        name : str
            Tool identifier.

        Returns:
        --------
        Tool or None : The matching Tool instance if found, else None.
        """
        return self._tools.get(name)

    def list_tools(self) -> List[Tool]:
        """Returns all registered Tool objects."""
        return list(self._tools.values())

    def get_prompt_catalog(self) -> str:
        """
        Generates the formatted string block listing all registered tools for the system prompt.

        Returns:
        --------
        str : Formatted catalog of tool definitions.
        """
        if not self._tools:
            return "No tools available."
        return "\n".join([tool.to_schema_prompt() for tool in self._tools.values()])

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Looks up and executes a tool with the provided arguments.

        Parameters:
        -----------
        tool_name : str
            The name of the tool to run.
        arguments : dict
            Arguments dictionary extracted from LLM JSON.

        Returns:
        --------
        str : The output result from tool execution.
        """
        tool = self.get(tool_name)
        if not tool:
            return f"Error: Tool '{tool_name}' is not registered in this agent's catalog."

        result = tool.execute(**arguments)
        return str(result)


# ==============================================================================
# SECTION 3: STANDARD BUILT-IN TOOL IMPLEMENTATIONS
# ==============================================================================

# --- File System Tools ---

def tool_list_files(path: str = ".") -> str:
    """Lists files and folders inside a given directory path."""
    try:
        entries = os.listdir(path)
        if not entries:
            return f"Directory '{path}' is empty."
        return "\n".join(entries)
    except Exception as e:
        return f"Failed to list directory '{path}': {e}"


def tool_read_file(path: str) -> str:
    """Reads the complete text content of a file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Failed to read file '{path}': {e}"


def tool_create_folder(path: str) -> str:
    """Creates a new directory path recursively."""
    try:
        os.makedirs(path, exist_ok=True)
        return f"Folder successfully created at: {path}"
    except Exception as e:
        return f"Failed to create folder '{path}': {e}"


def tool_create_file(path: str, content: str) -> str:
    """Creates a new text file and writes the specified content."""
    try:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File successfully written: {path} ({len(content)} characters)"
    except Exception as e:
        return f"Failed to write file '{path}': {e}"


def tool_delete_file(path: str) -> str:
    """Deletes a file from disk. Categorized as DANGEROUS."""
    try:
        if os.path.exists(path):
            os.remove(path)
            return f"File successfully deleted: {path}"
        return f"File does not exist: {path}"
    except Exception as e:
        return f"Failed to delete file '{path}': {e}"


# --- Safe Calculator Tool ---

def tool_calculate(expression: str) -> str:
    """Safely evaluates a math expression using AST parsing without eval()."""
    try:
        operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.Mod: operator.mod
        }

        def _eval_node(node):
            if isinstance(node, ast.Expression):
                return _eval_node(node.body)
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                return node.value
            if isinstance(node, ast.BinOp):
                left = _eval_node(node.left)
                right = _eval_node(node.right)
                op = operators.get(type(node.op))
                if op:
                    return op(left, right)
            raise ValueError(f"Unsupported syntax or operator: {type(node).__name__}")

        tree = ast.parse(expression, mode="eval")
        result = _eval_node(tree)
        return str(result)
    except Exception as e:
        return f"Calculation error: {e}"


# ==============================================================================
# SECTION 4: FACTORY HELPERS FOR STANDARD TOOLSETS
# ==============================================================================

def get_file_tools() -> List[Tool]:
    """Returns the suite of file management tools."""
    return [
        Tool(
            name="list_files",
            description="List files and directories in a path",
            func=tool_list_files,
            risk_level="SAFE",
            parameters={"path": "string path, default '.'"}
        ),
        Tool(
            name="read_file",
            description="Read content of a text file",
            func=tool_read_file,
            risk_level="SAFE",
            parameters={"path": "string file path"}
        ),
        Tool(
            name="create_folder",
            description="Create a directory path",
            func=tool_create_folder,
            risk_level="MODERATE",
            parameters={"path": "string folder path"}
        ),
        Tool(
            name="create_file",
            description="Create or overwrite a file with text content",
            func=tool_create_file,
            risk_level="MODERATE",
            parameters={"path": "string file path", "content": "text content"}
        ),
        Tool(
            name="delete_file",
            description="Permanently delete a file from disk",
            func=tool_delete_file,
            risk_level="DANGEROUS",
            parameters={"path": "string file path"}
        )
    ]


def get_calculator_tools() -> List[Tool]:
    """Returns the safe math calculator tool."""
    return [
        Tool(
            name="calculate",
            description="Evaluate an arithmetic expression safely",
            func=tool_calculate,
            risk_level="SAFE",
            parameters={"expression": "string arithmetic expression (e.g. '25 * 4')"}
        )
    ]
