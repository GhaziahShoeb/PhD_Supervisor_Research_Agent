import os
import asyncio
import re
import logging
from typing import Literal
from langchain_core.tools import tool

logger = logging.getLogger("professor_research.agent.tools")

# Prefer the async Tavily client to avoid blocking the event loop; fallback to the sync
# client wrapped in asyncio.to_thread if the async client isn't available.
try:
    from tavily import AsyncTavilyClient

    _tavily_client = AsyncTavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    _use_async_client = True
except ImportError:
    from tavily import TavilyClient

    _tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    _use_async_client = False

_SITE_ONLY_RE = re.compile(r"(?i)\bsite:[^\s]+")

def _has_search_terms(query: str) -> bool:
    if not query or not query.strip():
        return False
    cleaned = _SITE_ONLY_RE.sub(" ", query)
    return re.search(r"[A-Za-z0-9]", cleaned) is not None

@tool
async def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search"""
    logger.info(f"Executing internet_search: query='{query}', max_results={max_results}, topic='{topic}'")
    if not _has_search_terms(query):
        logger.warning(f"Search query rejected (no keywords): '{query}'")
        return "Error: Search query must include keywords, not just 'site:' filters."
    
    try:
        if _use_async_client:
            result = await _tavily_client.search(
                query,
                max_results=max_results,
                include_raw_content=include_raw_content,
                topic=topic,
            )
        else:
            result = await asyncio.to_thread(
                _tavily_client.search,
                query,
                max_results,
                include_raw_content,
                topic,
            )
        logger.info(f"internet_search completed for query='{query}'")
        return result
    except Exception as e:
        logger.error(f"Error in internet_search: {e}")
        raise e

@tool
async def read_file(file_path: str):
    """Read a file from the filesystem."""
    logger.info(f"Reading file: {file_path}")
    def _read():
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    try:
        content = await asyncio.to_thread(_read)
        logger.info(f"Successfully read file: {file_path}")
        return content
    except Exception as e:
        logger.error(f"Error reading file '{file_path}': {e}")
        return f"Error reading file: {e}"

@tool
async def write_file(file_path: str, content: str):
    """Write content to a file. Overwrites if exists."""
    logger.info(f"Writing to file: {file_path}")
    def _write():
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"

    try:
        result = await asyncio.to_thread(_write)
        logger.info(f"Successfully wrote to file: {file_path}")
        return result
    except Exception as e:
        logger.error(f"Error writing to file '{file_path}': {e}")
        return f"Error writing file: {e}"

