from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Paletta FastAPI Web Application",
    description="A demo web application for the Paletta project using FastAPI",
    version="1.0.0"
)

templates = Jinja2Templates(directory="templates")

# determine the path to the static directory relative to this file
static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":

    import uvicorn
    uvicorn.run("paletta_code.app.main:app", host="127.0.0.1", port=8000, reload=True)
