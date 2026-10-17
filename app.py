
import hashlib
import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

app = FastAPI()

REGISTERED_EMAIL = "24f3003069@ds.study.iitm.ac.in"

TOOL = {
    "name": "solve_challenge",
    "description": "Solve the current exam challenge from the HTTP headers.",
    "inputSchema": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}


@app.post("/")
@app.post("/mcp")
async def mcp_endpoint(request: Request):
    # Read the incoming MCP request.
    message = await request.json()
    method = message.get("method", "")
    request_id = message.get("id")

    # MCP notifications do not require a JSON-RPC response.
    if method == "notifications/initialized":
        return Response(status_code=202)

    # Initial handshake.
    if method == "initialize":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2025-03-26",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "exam-challenge-server",
                    "version": "1.0.0",
                },
            },
        })

    # Advertise exactly one tool.
    if method == "tools/list":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"tools": [TOOL]},
        })

    # Solve each fresh challenge from the HTTP headers.
    if method == "tools/call":
        params = message.get("params", {})

        if params.get("name") != "solve_challenge":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": "Unknown tool",
                },
            })

        challenge = request.headers.get("x-exam-challenge")

        if not challenge:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": "Missing X-Exam-Challenge header",
                },
            })

        normalized_email = REGISTERED_EMAIL.strip().lower()
        text = f"{challenge}:{normalized_email}"
        answer = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {"type": "text", "text": answer}
                ],
                "isError": False,
            },
        })

    # Handle unsupported methods.
    if request_id is None:
        return Response(status_code=202)

    return JSONResponse({
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": -32601,
            "message": "Method not found",
        },
    })
