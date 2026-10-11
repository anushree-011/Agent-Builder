"""
==============================================================================
V11 - MULTI-AGENT SYSTEM: TOOLS MODULE
==============================================================================
Concept & Architecture:
This module contains the concrete executable tool implementations utilized by the
specialist agents in the Multi-Agent System (v11):
1. File Tools:
   - `list_files(path)`: Discovers directory contents.
   - `read_file(path)`: Reads text documents.
   - `create_folder(path)`: Recursively provisions folders.
   - `create_file(path, content)`: Creates files and writes UTF-8 text safely.
2. Memory Tools:
   - `save_memory(text)`: Appends knowledge to shared memory list.
   - `search_memory(keyword)`: Keyword lookup across recorded memories.
   - `show_memories()`: Inspects entire memory record.
3. Calculator Tool:
   - `calculate(expression)`: Safe arithmetic evaluator using Python Abstract Syntax
     Tree (`ast`), preventing remote code execution (RCE) hazards.
==============================================================================
"""

# Import the standard os module for file and directory system operations
import os

# Import ast module to safely parse expressions into abstract syntax trees
import ast

# Import operator module providing standard arithmetic operator mappings
import operator


# ==============================================================================
# SECTION 1: FILE SYSTEM TOOLS
# ==============================================================================

def list_files(path="."):
    """
    Lists files and directories contained within the specified path.

    Parameters:
    -----------
    path : str, default="."
        The directory path to inspect.

    Returns:
    --------
    str : A newline-delimited list of filenames, an empty notification, or error message.
    """
    try:
        # Retrieve all directory entries using os.listdir
        items = os.listdir(path)

        # Handle empty folder scenario
        if not items:
            return "The folder is empty."

        # Return entries formatted as newline-separated text
        return "\n".join(items)

    except Exception as error:
        # Catch and report any I/O or filesystem errors
        return f"Error listing files: {error}"


def read_file(path):
    """
    Reads and returns the complete text content of a specified file.

    Parameters:
    -----------
    path : str
        The relative or absolute file path to read.

    Returns:
    --------
    str : File contents string or descriptive error message.
    """
    try:
        # Open file in read mode with UTF-8 character encoding
        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:
            return file.read()

    except Exception as error:
        # Catch and return error if file is missing or unreadable
        return f"Error reading file: {error}"


def create_folder(path):
    """
    Creates a new directory path, including any intermediate parent directories.

    Parameters:
    -----------
    path : str
        Directory path to create.

    Returns:
    --------
    str : Confirmation message upon creation or error description.
    """
    try:
        # Create directories with exist_ok=True to avoid errors if already present
        os.makedirs(
            path,
            exist_ok=True
        )

        return f"Folder created successfully: {path}"

    except Exception as error:
        # Return error details if creation fails
        return f"Error creating folder: {error}"


def create_file(path, content):
    """
    Creates a new file with text content, automatically creating any missing parent folders.

    Parameters:
    -----------
    path : str
        Path of the file to write.
    content : str
        Text content to write into the file.

    Returns:
    --------
    str : Success confirmation message or error details.
    """
    try:
        # Determine parent folder from target file path
        parent = os.path.dirname(path)

        # If parent folder path exists and is not yet created, create it
        if parent:
            os.makedirs(
                parent,
                exist_ok=True
            )

        # Write text content with UTF-8 encoding
        with open(
            path,
            "w",
            encoding="utf-8"
        ) as file:
            file.write(content)

        return f"File created successfully: {path}"

    except Exception as error:
        # Return descriptive error on write failure
        return f"Error creating file: {error}"


# ==============================================================================
# SECTION 2: IN-MEMORY STORAGE TOOLS
# ==============================================================================

# In-memory storage list holding text memories
memory = []


def save_memory(text):
    """
    Stores a text fact or knowledge item into the memory store.

    Parameters:
    -----------
    text : str
        Text string to store.

    Returns:
    --------
    str : Confirmation message.
    """
    # Append memory item
    memory.append(text)

    return f"Memory saved: {text}"


def search_memory(keyword):
    """
    Finds and returns all memories containing the specified keyword (case-insensitive).

    Parameters:
    -----------
    keyword : str
        The query term to search for.

    Returns:
    --------
    str : Newline-delimited list of matching memories or notice if no matches.
    """
    results = []

    # Iterate through all saved items
    for item in memory:
        # Check case-insensitive match
        if keyword.lower() in item.lower():
            results.append(item)

    # If no results matched
    if not results:
        return "No matching memories found."

    # Return matching results
    return "\n".join(results)


def show_memories():
    """
    Returns all stored memories in the system.

    Returns:
    --------
    str : Newline-delimited string of all memories or message if empty.
    """
    # Check if empty
    if not memory:
        return "No memories stored."

    # Join and return
    return "\n".join(memory)


# ==============================================================================
# SECTION 3: SAFE ARITHMETIC EVALUATION VIA AST
# ==============================================================================

def calculate(expression):
    """
    Safely evaluates a basic mathematical expression using Python's Abstract Syntax Tree (AST).

    Security Note:
    Avoids arbitrary code execution vulnerabilities associated with `eval()` by
    strictly validating syntax and only evaluating numeric literals and safe binary operations.

    Parameters:
    -----------
    expression : str
        Mathematical formula string (e.g. '25 * 8', '100 / (4 + 1)').

    Returns:
    --------
    str : String representation of the numeric result, or calculation error message.
    """
    try:
        # Mapping of AST operator types to standard operator functions
        allowed_operators = {
            ast.Add: operator.add,        # Addition (+)
            ast.Sub: operator.sub,        # Subtraction (-)
            ast.Mult: operator.mul,       # Multiplication (*)
            ast.Div: operator.truediv,    # Division (/)
            ast.Pow: operator.pow,        # Exponentiation (**)
            ast.Mod: operator.mod         # Modulo (%)
        }

        def evaluate(node):
            """
            Recursive evaluator for safe AST nodes.
            """
            # If root expression node, evaluate its inner expression body
            if isinstance(node, ast.Expression):
                return evaluate(node.body)

            # If constant number literal, return the value directly
            if isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    return node.value

            # If binary arithmetic operation (Left OP Right)
            if isinstance(node, ast.BinOp):
                left = evaluate(node.left)
                right = evaluate(node.right)

                # Look up operation from whitelist
                operation = allowed_operators.get(type(node.op))

                if operation:
                    return operation(left, right)

            # Disallow any other node type (e.g., function calls, attributes, identifiers)
            raise ValueError("Unsupported expression or operation")

        # Parse string expression into AST in eval mode
        tree = ast.parse(expression, mode="eval")

        # Evaluate tree safely
        result = evaluate(tree)

        # Return result as string
        return str(result)

    except Exception as error:
        # Catch and report arithmetic or parsing errors
        return f"Calculation error: {error}"