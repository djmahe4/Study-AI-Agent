"""
Client for the free-llm-apis MCP server.

The free-llm-apis server must be started in SSE/HTTP mode:
    cd /home/kali/Desktop/awesome-free-llm-apis/mcp-server
    npx tsx src/server.ts --sse

    Or build first then run:
    npm run build
    node dist/src/server.js --sse

It then exposes http://localhost:3000/mcp (StreamableHTTP MCP endpoint).
Port is configurable via the MCP_FREE_LLM_HOST env var.
"""

import httpx
import json
import uuid
from typing import Optional
from config import settings

FREE_LLM_BASE = getattr(settings, "FREE_LLM_HOST", "http://localhost:3000")
MCP_ENDPOINT  = f"{FREE_LLM_BASE}/mcp"

# ─ Structured output prompt ───────────────────────────────────────────────────
EDUCATIONAL_SYSTEM = """
You are an expert computer science tutor specialising in algorithmic thinking.
When answering ANY learning question you MUST produce a response in exactly
three clearly labelled sections:

## 🔍 Concept Explanation
A clear, concise explanation of the concept or algorithm.

## 🐍 Python Script
A self-contained, runnable Python script that demonstrates or solves the
problem. Include inline comments explaining every major step.
The code must work on Python 3.10+ with no external dependencies unless
absolutely necessary.

```python
# ... code here
```

## 🗺️ Mermaid Diagram
A Mermaid diagram (flowchart or sequence) that visually explains the algorithm
or data flow. Use the ```mermaid code fence.

```mermaid
flowchart TD
    ...
```

IMPORTANT: Always include all three sections, even for simple topics.
""".strip()


async def call_free_llm(message: str, session_id: Optional[str] = None) -> str:
    """
    Call the free-llm-apis server's `use_free_llm` tool over StreamableHTTP.
    Falls back to a descriptive error string if the server is unreachable.
    """
    sid = session_id or str(uuid.uuid4())
    
    # MCP tool call payload (JSON-RPC 2.0)
    payload = {
        "jsonrpc": "2.0",
        "id": sid,
        "method": "tools/call",
        "params": {
            "name": "use_free_llm",
            "arguments": {
                "messages": [
                    {"role": "system", "content": EDUCATIONAL_SYSTEM},
                    {"role": "user",   "content": message}
                ],
                "agentic": False,          # keep lightweight for chat use
            }
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept":        "application/json, text/event-stream",
    }
    
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            # 1. Initialize session (required by StreamableHTTP transport)
            init_payload = {
                "jsonrpc": "2.0", "id": "init",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "study-ai-mcp-client", "version": "1.0"}
                }
            }
            init_resp = await client.post(MCP_ENDPOINT, json=init_payload, headers=headers)
            mcp_session_id = init_resp.headers.get("mcp-session-id")
            
            call_headers = dict(headers)
            if mcp_session_id:
                call_headers["mcp-session-id"] = mcp_session_id
            
            # 2. Call the tool
            resp = await client.post(MCP_ENDPOINT, json=payload, headers=call_headers)
            resp.raise_for_status()
            
            # 3. Parse response — may be JSON or newline-delimited SSE
            content_type = resp.headers.get("content-type", "")
            if "text/event-stream" in content_type:
                # Collect streamed JSON-RPC response lines
                result_text = ""
                for line in resp.text.splitlines():
                    line = line.strip()
                    if line.startswith("data:"):
                        data = line[5:].strip()
                        if data and data != "[DONE]":
                            try:
                                obj = json.loads(data)
                                # Navigate MCP result structure
                                result = obj.get("result", {})
                                for item in result.get("content", []):
                                    if item.get("type") == "text":
                                        result_text += item["text"]
                            except json.JSONDecodeError:
                                pass
                return result_text or "[No content returned from free-llm-apis]"
            else:
                obj = resp.json()
                result = obj.get("result", {})
                parts = result.get("content", [])
                return "\n".join(p["text"] for p in parts if p.get("type") == "text") \
                    or str(result)
                    
    except httpx.ConnectError:
        return (
            "⚠️ **free-llm-apis server is not running.**\n\n"
            "Start it with:\n```bash\n"
            "cd /home/kali/Desktop/awesome-free-llm-apis/mcp-server\n"
            "node dist/src/server.js --sse\n```"
        )
    except Exception as e:
        return f"⚠️ Error calling free-llm-apis: {e}"
