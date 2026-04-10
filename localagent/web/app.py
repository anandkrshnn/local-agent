import os
import json
import asyncio
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from localagent.agent import LocalAgent
import uvicorn

app = FastAPI(title="LocalAgent Dashboard")

# Paths
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Shared agent instance
agent = LocalAgent()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    stats = agent.get_stats()
    return templates.TemplateResponse("index.html", {"request": request, "stats": stats})

@app.post("/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        user_input = data.get("message", "")
        if not user_input:
            return {"response": "Please enter a message."}
        
        response = agent.chat(user_input)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/stream")
async def chat_stream(request: Request):
    """Character-by-character response streaming."""
    data = await request.json()
    user_input = data.get("message", "").strip()

    if not user_input:
        return {"response": "Please enter a message."}

    # Execute synchronously but stream the response (simulated typing)
    try:
        full_response = agent.chat(user_input)
    except Exception as e:
        full_response = f"Error: {str(e)}"

    async def event_generator():
        for i in range(0, len(full_response), 3):  # 3 chars per chunk
            chunk = full_response[i:i+3]
            yield f"data: {json.dumps({'delta': chunk})}\n\n"
            await asyncio.sleep(0.018)
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/stats")
async def get_stats():
    try:
        return agent.get_stats()
    except Exception as e:
        return {"error": str(e)}

@app.get("/audit")
async def get_audit():
    """Expose recent audit log entries for the dashboard."""
    try:
        rows = agent.broker.conn.execute("""
            SELECT timestamp, intent, resource, granted, reason 
            FROM audit_log 
            ORDER BY timestamp DESC 
            LIMIT 50
        """).fetchall()
        
        audit = [
            {
                "timestamp": r[0],
                "intent": r[1],
                "resource": r[2],
                "granted": bool(r[3]),
                "reason": r[4] or ""
            }
            for r in rows
        ]
        return {"audit": audit}
    except Exception as e:
        return {"audit": [], "error": str(e)}

@app.get("/trust_status")
async def get_trust_status():
    """Return currently learned (confirmation-disabled) patterns."""
    learned = []
    for intent, policy in agent.broker.policies.items():
        if not policy.get("requires_confirmation", True):
            learned.append({
                "intent": intent,
                "reason": "Auto-learned from repeated approvals"
            })
    return {"learned_policies": learned}

@app.get("/sandbox_files")
async def get_sandbox_files():
    """Return list of files in the sandbox (recursive, limited for performance)"""
    try:
        files = []
        for item in agent.sandbox.root.rglob("*"):
            if item.is_file():
                files.append({
                    "name": item.name,
                    "path": str(item.relative_to(agent.sandbox.root)),
                    "size_kb": round(item.stat().st_size / 1024, 1),
                    "modified": item.stat().st_mtime
                })
        return {"files": files[:100]}  # Limit to 100 entries
    except Exception as e:
        return {"files": [], "error": str(e)}

@app.on_event("shutdown")
def shutdown_event():
    agent.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
