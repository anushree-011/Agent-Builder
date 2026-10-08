import os
import ast
import operator


# ============================================================
# FILE TOOLS
# ============================================================

def list_files(path="."):
    """
    List files and folders inside a directory.
    """

    try:
        items = os.listdir(path)

        if not items:
            return "The folder is empty."

        return "\n".join(items)

    except Exception as e:
        return f"Error listing files: {e}"


def read_file(path):
    """
    Read the contents of a text file.
    """

    try:
        with open(path, "r", encoding="utf-8") as file:
            return file.read()

    except Exception as e:
        return f"Error reading file: {e}"


def create_folder(path):
    """
    Create a folder.
    """

    try:
        os.makedirs(path, exist_ok=True)
        return f"Folder created successfully: {path}"

    except Exception as e:
        return f"Error creating folder: {e}"


def create_file(path, content):
    """
    Create a file and write content into it.
    """

    try:
        parent = os.path.dirname(path)

        if parent:
            os.makedirs(parent, exist_ok=True)

        with open(path, "w", encoding="utf-8") as file:
            file.write(content)

        return f"File created successfully: {path}"

    except Exception as e:
        return f"Error creating file: {e}"


# ============================================================
# MEMORY TOOLS
# ============================================================

memory = []


def save_memory(text):
    """
    Save something into memory.
    """

    memory.append(text)

    return f"Memory saved: {text}"


def search_memory(keyword):
    """
    Search memories using a simple keyword.
    """

    results = []

    for item in memory:
        if keyword.lower() in item.lower():
            results.append(item)

    if not results:
        return "No matching memories found."

    return "\n".join(results)


def show_memories():
    """
    Show all saved memories.
    """

    if not memory:
        return "No memories stored."

    return "\n".join(memory)


# ============================================================
# CALCULATOR TOOL
# ============================================================

def calculate(expression):
    """
    Safely perform basic mathematical calculations.
    """

    try:

        allowed_operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.Mod: operator.mod,
        }

        def evaluate(node):

            if isinstance(node, ast.Expression):
                return evaluate(node.body)

            if isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    return node.value

            if isinstance(node, ast.BinOp):

                left = evaluate(node.left)
                right = evaluate(node.right)

                operation = allowed_operators.get(type(node.op))

                if operation:
                    return operation(left, right)

            raise ValueError("Unsupported expression")

        tree = ast.parse(expression, mode="eval")

        result = evaluate(tree)

        return str(result)

    except Exception as e:
        return f"Calculation error: {e}"