from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage  # Updated import
import json
from dotenv import load_dotenv
import httpx
import base64
import tempfile
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

required_env_vars = ["OPENAI_API_KEY"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the conversational AI model
llm = ChatOpenAI(
    model="gpt-4o-mini", 
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY")
)

logger.info("AI components initialized successfully")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    logger.info("New WebSocket connection request received")
    await websocket.accept()
    logger.info("WebSocket connection accepted")
    
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received message from client: {data}")
            message = json.loads(data)
            
            # Generate AI response (fixed async call)
            logger.info("Generating AI response...")
            response = await llm.ainvoke([HumanMessage(content=message["text"])])  # Use ainvoke
            message_content = response.content  # Direct access to content
            logger.info(f"AI response generated: {message_content}")
            
            # Convert text to speech
            tts_url = "https://api.openai.com/v1/audio/speech"
            headers = {
                'Authorization': f'Bearer {os.getenv("OPENAI_API_KEY")}',
                'Content-Type': 'application/json'
            }
            payload = {
                'model': 'tts-1',
                'voice': 'sage', 
                'input': message_content
            }
            
            async with httpx.AsyncClient() as client:
                tts_response = await client.post(tts_url, headers=headers, json=payload)
                
                # Stream audio chunks
                async for chunk in tts_response.aiter_bytes():
                    await websocket.send_bytes(chunk)
                    logger.info("Sent audio chunk to client")
                    
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {str(e)}", exc_info=True)
    finally:
        logger.info("WebSocket connection closed")


@app.post("/transcribe")
async def transcribe_audio(data: dict):
    try:
        audio_bytes = base64.b64decode(data['audio'])
        
        # temp file with WAV extension
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_audio.write(audio_bytes)
            temp_audio.flush()
            
            # Open as file-like object
            with open(temp_audio.name, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(  # Remove await
                    file=audio_file,
                    model="whisper-1",
                    response_format="text",
                    temperature=0.2,
                    prompt="ZKPs, Starknet, blockchain"
                )
        
        if not transcription.strip():
            raise HTTPException(400, "Empty transcription")
            
        return {"text": transcription.strip()}
    
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}") 
        raise HTTPException(500, f"Audio processing failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
