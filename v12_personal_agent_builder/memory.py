"""
==============================================================================
V12 - PERSONAL AGENT BUILDER: MEMORY SUBSYSTEM
==============================================================================
Concept & Architecture:
This module implements the dual-tiered memory system for the Personal Agent Builder:

1. Short-Term Working Memory:
   - Tracks recent conversational turns (user, assistant, system, tool).
   - Automatically maintains a sliding window buffer so token limits are respected.

2. Long-Term Persistent Memory:
   - Stores durable facts, preferences, and notes across multiple interactions.
   - Saves to a local JSON file store on disk (`agent_memory.json`).
   - Supports keyword search and listing.
   - Provides callable tool bindings (`save_memory`, `search_memory`, `show_memories`)
     so the agent can autonomously manage its own long-term memory!
==============================================================================
"""

import json
import os
from typing import List, Dict, Any, Optional
from tools import Tool


# ==============================================================================
# SECTION 1: SHORT-TERM CONVERSATIONAL BUFFER
# ==============================================================================

class ConversationBuffer:
    """
    Manages short-term working memory across conversational turns.
    """

    def __init__(self, max_turns: int = 10):
        """
        Initializes the conversation buffer.

        Parameters:
        -----------
        max_turns : int
            Maximum number of turns (user + assistant pairs) to preserve in memory.
        """
        self.max_turns = max_turns
        self.messages: List[Dict[str, str]] = []

    def add_message(self, role: str, content: str) -> None:
        """Adds a message to the buffer."""
        self.messages.append({"role": role, "content": content})
        self._trim()

    def _trim(self) -> None:
        """Trims old messages exceeding max_turns while preserving system prompt if first."""
        max_messages = self.max_turns * 2
        if len(self.messages) > max_messages:
            self.messages = self.messages[-max_messages:]

    def get_messages(self) -> List[Dict[str, str]]:
        """Returns the full list of buffered messages."""
        return list(self.messages)

    def clear(self) -> None:
        """Clears all conversation turns."""
        self.messages.clear()


# ==============================================================================
# SECTION 2: LONG-TERM PERSISTENT MEMORY STORE
# ==============================================================================

class PersistentMemoryStore:
    """
    File-backed persistent storage for facts, notes, and user preferences.
    """

    def __init__(self, storage_path: str = "agent_memory.json"):
        """
        Parameters:
        -----------
        storage_path : str
            JSON file path where memories will be loaded and saved.
        """
        self.storage_path = storage_path
        self.memories: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        """Loads memories from disk if the storage file exists."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.memories = data
            except Exception as e:
                print(f"[Memory Warning] Failed to load memories from {self.storage_path}: {e}")
                self.memories = []
        else:
            self.memories = []

    def _save(self) -> None:
        """Flushes memory records to the persistent JSON file."""
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.memories, f, indent=2)
        except Exception as e:
            print(f"[Memory Error] Failed to persist memory to {self.storage_path}: {e}")

    def save_fact(self, text: str, category: str = "general") -> str:
        """
        Saves a new fact into persistent memory.

        Parameters:
        -----------
        text : str
            Fact or note to record.
        category : str
            Optional classification tag.

        Returns:
        --------
        str : Confirmation message.
        """
        entry = {
            "id": len(self.memories) + 1,
            "category": category,
            "content": text
        }
        self.memories.append(entry)
        self._save()
        return f"Fact saved to long-term memory (ID: {entry['id']}): '{text}'"

    def search_facts(self, query: str) -> str:
        """
        Searches memories matching the query substring.

        Parameters:
        -----------
        query : str
            Keyword to search for.

        Returns:
        --------
        str : Newline-separated matching facts or message if none found.
        """
        query_lower = query.lower()
        matches = [
            f"[{item.get('category', 'general')}] {item['content']}"
            for item in self.memories
            if query_lower in item['content'].lower()
        ]
        if not matches:
            return f"No memories found matching '{query}'."
        return "\n".join(matches)

    def list_all_facts(self) -> str:
        """
        Lists all memories stored in the system.

        Returns:
        --------
        str : Formatted text of all stored items.
        """
        if not self.memories:
            return "No persistent memories currently stored."
        return "\n".join([
            f"- [{item.get('category', 'general')}] {item['content']}"
            for item in self.memories
        ])

    def get_as_tools(self) -> List[Tool]:
        """
        Constructs and returns executable Tool wrappers for agent invocation.

        Returns:
        --------
        List[Tool] : Tools for save_memory, search_memory, and show_memories.
        """
        return [
            Tool(
                name="save_memory",
                description="Save an important fact or user preference into long-term memory",
                func=lambda text, category="general": self.save_fact(text, category),
                risk_level="SAFE",
                parameters={"text": "string fact to record", "category": "optional category tag"}
            ),
            Tool(
                name="search_memory",
                description="Search long-term memory for past facts or user preferences by keyword",
                func=lambda keyword: self.search_facts(keyword),
                risk_level="SAFE",
                parameters={"keyword": "string keyword to look up"}
            ),
            Tool(
                name="show_memories",
                description="Show all recorded facts and memories currently stored",
                func=lambda: self.list_all_facts(),
                risk_level="SAFE",
                parameters={}
            )
        ]
