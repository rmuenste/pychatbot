import os
import logging
from fastapi import FastAPI, Form, Request, WebSocket
from typing import Annotated
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
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

            aiResponse = ""
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    aiResponse += chunk.choices[0].delta.content
                    await websocket.send_text(chunk.choices[0].delta.content)

            chatResponses.append(aiResponse)

        except Exception as e:
            # Send data back to client
            await websocket.send_text(f'Error: {str(e)}')    
            logger.error(e)


            #botResponse = response.choices[0].message.content
            #chatLog.append({"role": "assistant", "content": aiResponse})

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
