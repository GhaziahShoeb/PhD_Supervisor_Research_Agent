# main.py
import asyncio
import json
import logging
import uuid
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langgraph.types import Overwrite
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
from agent import agent

# Configure logging for the API
logger = logging.getLogger("professor_research.agent.api")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

app = FastAPI(title="Professor Research API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ResearchRequest(BaseModel):
    user_id: Optional[str] = "default_user"
    concatenated_query: str

async def research_stream_generator(request: ResearchRequest):
    inputs = {"messages": [("user", request.concatenated_query)]}
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id, "user_id": request.user_id}}
    
    last_final_content = None

    try:
        # Initial event to confirm connection
        logger.info("New research stream opened: thread_id=%s user_id=%s query=%s", thread_id, request.user_id, request.concatenated_query)
        yield f"data: {json.dumps({'type': 'connection', 'status': 'connected', 'thread_id': thread_id})}\n\n"

        # stream_mode="updates" yields the state updates from each node
        async for event in agent.astream(inputs, config=config, stream_mode="updates"):
            logger.debug("Received event from agent.astream: %s", event)
            for node_name, node_output in event.items():
                # Notify frontend which agent is active
                logger.info("Agent active: %s (thread=%s)", node_name, thread_id)
                yield f"data: {json.dumps({'type': 'agent_active', 'agent': node_name})}\n\n"

                if not node_output:
                    logger.debug("No output for node: %s", node_name)
                    continue

                messages = node_output.get("messages", [])
                if isinstance(messages, Overwrite):
                    messages = messages.value
                if not isinstance(messages, list):
                    messages = [messages]

                for msg in messages:
                    # Handle AI Thoughts & Tool Calls
                    if isinstance(msg, AIMessage):
                        if msg.content:
                            logger.info("[%s] Thought: %s", node_name, (msg.content[:200] + '...') if len(msg.content) > 200 else msg.content)
                            yield f"data: {json.dumps({'type': 'thought', 'agent': node_name, 'content': msg.content})}\n\n"

                        for tool_call in getattr(msg, 'tool_calls', []) or []:
                            logger.info("[%s] Tool call: %s args=%s", node_name, tool_call.get('name'), tool_call.get('args'))
                            yield f"data: {json.dumps({'type': 'tool_call', 'agent': node_name, 'tool': tool_call['name'], 'args': tool_call['args']})}\n\n"

                    # Handle Tool Outputs
                    elif isinstance(msg, ToolMessage):
                        content_preview = msg.content[:500] + '...' if len(str(msg.content)) > 500 else msg.content
                        logger.info("[%s] Tool result: %s -> %s", node_name, msg.name, (str(content_preview)[:200] + '...') if len(str(content_preview)) > 200 else content_preview)
                        yield f"data: {json.dumps({'type': 'tool_result', 'agent': node_name, 'tool': msg.name, 'content': content_preview})}\n\n"

                    # Capture final report if this is the lead agent
                    if node_name == "academic-research-lead" and isinstance(msg, AIMessage) and msg.content:
                        # We assume the lead's last message is the report
                        logger.info("Lead generated final content (preview): %s", (msg.content[:200] + '...') if len(msg.content) > 200 else msg.content)
                        last_final_content = msg.content

        # Send the final result
        if last_final_content:
            yield f"data: {json.dumps({'type': 'final', 'content': last_final_content})}\n\n"
        else:
             yield f"data: {json.dumps({'type': 'final', 'content': 'No report generated.'})}\n\n"

        yield "data: [DONE]\n\n"

    except Exception as e:
        logger.exception("Error in research_stream_generator: %s", e)
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

@app.post("/research/stream")
async def run_research_stream(request: ResearchRequest):
    return StreamingResponse(research_stream_generator(request), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting uvicorn server for Professor Research API")
    uvicorn.run(app, host="0.0.0.0", port=8000)