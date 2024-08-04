"""
python -m venv env
# Activate the environment:
#
# On Windows:
.\env\Scripts\activate
#
# On macOS/Linux:
source env/bin/activate
#
# Install the requirements:
pip install -r requirements.txt

# Run the application by using the following command:
uvicorn main:app --reload
"""
import os
import logging
from fastapi import FastAPI, Form, Request, WebSocket
from typing import Annotated
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Template
from dotenv import load_dotenv
import openai
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Retrieve OpenAI API key from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")

# Create OpenAI client with API key
client = OpenAI(api_key=openai_api_key)

# Configure logging module to log INFO level and above messages
logging.basicConfig(level=logging.INFO)

# Create logger for the current module
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create Jinja2 templates rendering engine with templates directory as the source
templates = Jinja2Templates(directory="templates")

# Initialize chat log with a system message
chatLog = [{"role": "system", "content": "You are a helpful assistant."}]

# Initialize chat responses as an empty list
chatResponses = []

#==============================================================================
# @app Startup
#==============================================================================
@app.on_event("startup")
async def startup_event():
    logger.info("Application startup complete.")

#==============================================================================
# @app Shutdown
#==============================================================================
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown complete.")

#==============================================================================
# @app.get("/")
#==============================================================================
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
#    template = Template("<h1>Hello, {{ name }}!</h1>")
#    html_content = template.render(name="FastAPI")
    return templates.TemplateResponse("home.html", {"request": request, "chatResponses": chatResponses, "chatLog": chatLog})

#==============================================================================
# @app.get("/openai")
#==============================================================================
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

#==============================================================================
# @app.websocker("/ws")
#==============================================================================
@app.websocket("/ws")
async def websocketChat(websocket: WebSocket):

    await websocket.accept()

    while True:
        # Get data from client
        userInput = await websocket.receive_text()
        chatLog.append({"role": "user", "content": userInput})        
        chatResponses.append(userInput)

        try:
            # Make a simple request to OpenAI API
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=chatLog,
                stream=True
            )

            chunkCounter = 0

            # We will sit in this loop and await the stream of responses
            # See here for more info:
            # https://cookbook.openai.com/examples/how_to_stream_completions
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    aiResponse += chunk.choices[0].delta.content
                    await websocket.send_text(chunk.choices[0].delta.content) 
                    # Increment the chunk counter
                    chunkCounter += 1

        except Exception as e:
            # Send data back to client
            await websocket.send_text(f'Error: {str(e)}')    
            logger.error(e)

        # Append the assistant's response to the chat log
        chatLog.append({"role": "assistant", "content": aiResponse})
        chatResponses.append(aiResponse)

#==============================================================================
# @app.post("/chat")
#==============================================================================
@app.post("/chat", response_class=HTMLResponse)
async def callChat(request: Request, userInput: Annotated[str, Form()]):
    logger.info("Chat endpoint called.")
    chatLog.append({"role": "user", "content": userInput})
    chatResponses.append(userInput)
    # Make a simple request to OpenAI API
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=chatLog
    )


    botResponse = response.choices[0].message.content
    chatResponses.append(botResponse)
    chatLog.append({"role": "assistant", "content": botResponse})
    return templates.TemplateResponse("home.html", {"request": request, "chatResponses": chatResponses, "chatLog": chatLog})
    

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting uvicorn server")
    uvicorn.run(app, host="127.0.0.1", port=8000)
