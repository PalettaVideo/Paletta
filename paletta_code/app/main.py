from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .authentication import auth_router
from .user import user_router
from .database import engine, Base
import os

# initialise FastAPI app
app = FastAPI(
    title="Paletta FastAPI Web Application",
    description="A demo web application for the Paletta project using FastAPI",
    version="1.0.0"
)

# create database tables if they don’t exist
Base.metadata.create_all(bind=engine)

# creates the static path
static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")

# mounts the static files directory to the app
app.mount("/static", StaticFiles(directory=static_path), name="static")

# load HTML templates
templates = Jinja2Templates(directory="templates")

# include routers for authentication & user management
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(user_router, prefix="/users", tags=["Users"])

# serve index.html as the application root page
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
