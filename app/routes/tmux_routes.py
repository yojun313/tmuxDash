import asyncio
import json
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.services import tmux_service
from app.routes.auth_routes import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def index(request: Request):
    if not get_current_user(request):
        return RedirectResponse(url="/login", status_code=302)
    sessions = tmux_service.get_sessions()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"sessions": [s.to_dict() for s in sessions]},
    )


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # WebSocket은 쿠키로 토큰 검증
    from app.routes.auth_routes import verify_token

    token = websocket.cookies.get("access_token")
    if not verify_token(token):
        await websocket.close(code=1008)  # Policy Violation
        return

    await websocket.accept()
    try:
        while True:
            sessions = tmux_service.get_sessions()
            payload = [s.to_dict() for s in sessions]
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
