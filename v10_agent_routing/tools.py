"""
==============================================================================
V10 - AGENT ROUTING: TOOLS MODULE
==============================================================================
Concept & Purpose:
This module contains the executable tools called by the specialist agents:
1. File Tools:
   - list_files, read_file, create_folder, create_file
2. Memory Tools:
   - In-memory list storage, keyword search, display
3. Calculator Tool:
   - Secure mathematical evaluation using Python's Abstract Syntax Tree (AST).
   - Protects the host machine by explicitly avoiding dangerous `eval()`.
==============================================================================
"""

# Import os module for interacting with the local file system (directories, paths, files)
import os

# Import ast module to parse string expressions into Python abstract syntax tree nodes safely
import ast

# Import operator module to provide standard mathematical functions mapping to AST operations
import operator


# ==============================================================================
# SECTION 1: FILE SYSTEM TOOLS
# ==============================================================================

def list_files(path="."):
    """
    Lists all files and subdirectories inside the designated directory path.

    Parameters:
    -----------
    path : str, default="."
        The target directory path to list.

    Returns:
    --------
    str : Newline-separated list of items, or a notification if empty/error.
    """
    try:
        # Query directory contents using os.listdir
        items = os.listdir(path)

        # Check if the folder is completely empty
        if not items:
            return "The folder is empty."

        # Format items into a clean newline-separated string
        return "\n".join(items)

    except Exception as e:
        # Catch and return any file-system errors (e.g., directory not found, permission denied)
        return f"Error listing files: {e}"


def read_file(path):
    """
    Reads and returns the complete text content of a specified file.

    Parameters:
    -----------
    path : str
        Relative or absolute path of the file to read.

    Returns:
    --------
    str : Text content of the file or error description.
    """
    try:
        # Open file in read mode with UTF-8 character encoding
        with open(path, "r", encoding="utf-8") as file:
            return file.read()

    except Exception as e:
        # Gracefully handle missing file or read permissions
        return f"Error reading file: {e}"


def create_folder(path):
    """
    Creates a new directory (including any missing parent directories).

    Parameters:
    -----------
    path : str
        The path of the directory to create.

    Returns:
    --------
    str : Success confirmation message or error description.
    """
    try:
        # Use makedirs with exist_ok=True so it does not fail if directory already exists
        os.makedirs(path, exist_ok=True)
        return f"Folder created successfully: {path}"

    except Exception as e:
        # Return error details if creation fails
        return f"Error creating folder: {e}"


def create_file(path, content):
    """
    Creates a new file and writes text content into it. Automatically creates parent directories.

    Parameters:
    -----------
    path : str
        The target file path.
    content : str
        The text content to write into the file.

    Returns:
    --------
    str : Success confirmation message or error description.
    """
    try:
        # Extract the directory portion of the file path
        parent = os.path.dirname(path)

        # If parent folder is specified and does not exist yet, create it
        if parent:
            os.makedirs(parent, exist_ok=True)

        # Write text to the file using UTF-8 encoding
        with open(path, "w", encoding="utf-8") as file:
            file.write(content)

        return f"File created successfully: {path}"

    except Exception as e:
        # Return error message on failure
        return f"Error creating file: {e}"


# ==============================================================================
# SECTION 2: IN-MEMORY TOOLS
# ==============================================================================

# Global in-memory list to store text memories across agent interactions
memory = []


def save_memory(text):
    """
    Appends a new text fact or memory into the global memory list.

    Parameters:
    -----------
    text : str
        The memory string to record.

    Returns:
    --------
    str : Confirmation message.
    """
    # Append the text to memory list
    memory.append(text)
    return f"Memory saved: {text}"


def search_memory(keyword):
    """
    Searches the stored memories for occurrences containing the given keyword (case-insensitive).

    Parameters:
    -----------
    keyword : str
        The search term to match against memories.

    Returns:
    --------
    str : Newline-separated matching memories or notice if none matched.
    """
    results = []

    # Iterate over all stored memory items
    for item in memory:
        # Check if keyword is a case-insensitive substring
        if keyword.lower() in item.lower():
            results.append(item)

    # Check if any matches were found
    if not results:
        return "No matching memories found."

    # Return matching results separated by newlines
    return "\n".join(results)


def show_memories():
    """
    Retrieves and displays all currently stored memories.

    Returns:
    --------
    str : Formatted string of all memories or message indicating memory is empty.
    """
    # Check if list is empty
    if not memory:
        return "No memories stored."

    # Return all memories joined by newlines
    return "\n".join(memory)


# ==============================================================================
# SECTION 3: SAFE CALCULATOR TOOL (AST-BASED)
# ==============================================================================

def calculate(expression):
    """
    Safely evaluates a basic mathematical expression using an Abstract Syntax Tree (AST).
    
    Security Design:
    Never use `eval()` on raw user or LLM input, as it allows arbitrary code execution.
    AST evaluation parses the code structure into a tree and ONLY executes allowed operators
    on numbers.

    Parameters:
    -----------
    expression : str
        The arithmetic expression (e.g., '25 * 8 + (10 / 2)').

    Returns:
    --------
    str : String representation of the calculated number or error message.
    """
    try:
        # Whitelist of permitted binary arithmetic operators
        allowed_operators = {
            ast.Add: operator.add,       # Addition (+)
            ast.Sub: operator.sub,       # Subtraction (-)
            ast.Mult: operator.mul,      # Multiplication (*)
            ast.Div: operator.truediv,   # True division (/)
            ast.Pow: operator.pow,       # Exponentiation (**)
            ast.Mod: operator.mod,       # Modulo (%)
        }

        def evaluate(node):
            """
            Recursively traverses and evaluates safe AST nodes.
            """
            # If top-level expression wrapper, evaluate the inner expression body
            if isinstance(node, ast.Expression):
                return evaluate(node.body)

            # If constant numeric value (int or float), return it directly
            if isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    return node.value

            # If binary operation (e.g. A + B), evaluate both sides and apply operator
            if isinstance(node, ast.BinOp):
                left = evaluate(node.left)
                right = evaluate(node.right)

                # Look up operator in whitelist
                operation = allowed_operators.get(type(node.op))
                if operation:
                    return operation(left, right)

            # Reject any unsupported node type (e.g., function calls, variable lookups, imports)
            raise ValueError("Unsupported expression or operation")

        # Parse string into an AST with mode="eval"
        tree = ast.parse(expression, mode="eval")

        # Evaluate the syntax tree
        result = evaluate(tree)

        # Return string result
        return str(result)

    except Exception as e:
        # Return safe calculation error message
        return f"Calculation error: {e}"