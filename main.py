import os
import logging
from fastapi import FastAPI, Form, Request
from typing import Annotated
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from jinja2 import Template
from dotenv import load_dotenv
import openai
from openai import OpenAI

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=openai_api_key)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI()

templates = Jinja2Templates(directory="templates")

chatLog = [{"role": "system", "content": "You are a helpful assistant."}]

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup complete.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown complete.")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
#    template = Template("<h1>Hello, {{ name }}!</h1>")
#    html_content = template.render(name="FastAPI")
    return templates.TemplateResponse("layout.html", {"request": request})

@app.get("/openai")
async def call_openai(userInput):
    logger.info("OpenAI endpoint called.")

    chatLog.append({"role": "user", "content": userInput})
    
    # Make a simple request to OpenAI API
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=chatLog
    )

    botResponse = response.choices[0].message.content
    chatLog.append({"role": "assistant", "content": botResponse})
    
    return {"response": response, "chatLog": chatLog}    

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting uvicorn server")
    uvicorn.run(app, host="127.0.0.1", port=8000)
