import os
import logging
from fastapi import FastAPI
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

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup complete.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown complete.")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    template = Template("<h1>Hello, {{ name }}!</h1>")
    html_content = template.render(name="FastAPI")
    return html_content

@app.get("/openai")
async def call_openai():
    logger.info("OpenAI endpoint called.")
    
    # Make a simple request to OpenAI API
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role": "system", "content": "You are a helpful assistant."
        }, {
            "role": "user", "content": "Who won the tennis tournament Roland Garros in 2019?"
        }]
    )
    
    return {"response": response}    

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting uvicorn server")
    uvicorn.run(app, host="127.0.0.1", port=8000)
