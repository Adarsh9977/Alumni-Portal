import sys
import traceback

try:
    from app.main import app
except Exception as e:
    from fastapi import FastAPI
    from fastapi.responses import PlainTextResponse
    
    app = FastAPI()
    
    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
    def catch_all(path: str):
        return PlainTextResponse(traceback.format_exc(), status_code=500)
