from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from app.routes import tmux_routes, auth_routes

app = FastAPI(title="Tmux Viewer")

app.include_router(auth_routes.router)
app.include_router(tmux_routes.router)
