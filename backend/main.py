from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from langchain_community.tools import ElevenLabsText2SpeechTool
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
import json
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import play
import requests

load_dotenv()



# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

required_env_vars = ["ELEVEN_API_KEY", "OPENAI_API_KEY"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

app = FastAPI()

client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI components
logger.info("Initializing AI components...")

# Use ChatOpenAI instead of OpenAI
llm = ChatOpenAI(
    model="gpt-4o-mini", 
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY")
)
tts = ElevenLabsText2SpeechTool(
    api_key=os.getenv("ELEVEN_API_KEY")
)

# Create LangGraph agent with compatible model
agent = create_react_agent(
    model=llm,
    tools=[tts],
    messages_modifier="You are a Starkchan the zero-knowledge proofs waifu, a metaverse entertainer that knows a lot about ZKPs and Starknet, and can make witty replies. IMPORTANT: Keep it conversational, so make sure to only give short answers and make your output digestible for T2S! Example convo: User: 'I like your curves!' You:'Thanks they are eliptic!'"
)

logger.info("AI components initialized successfully")
def text_to_speech(text, api_key):
    url = "https://api.elevenlabs.io/v1/text-to-speech/21m00tcm4tlvdq8ikwam"  # Using a default voice ID
    
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    data = {
        "text": text,
        "voice_settings": {
            "stability": 0.7,
            "similarity_boost": 0.8
        }
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    # Save the audio file
    output_path = "output.mp3"
    with open(output_path, "wb") as f:
        f.write(response.content)
    
    return output_path

# Update your websocket endpoint to use the new function:
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
            
            # Generate AI response using LangGraph agent
            logger.info("Generating AI response...")
            response = agent.invoke({"messages": [("user", message["text"])]})
            logger.info(f"AI response generated: {response}")
            
            # Get the last message content
            ai_message = response["messages"][-1]
            message_content = ai_message.content
            
            # Convert to speech using the new API
            logger.info("Converting text to speech...")
            audio_generator = client.text_to_speech.convert(
                text=message_content,
                voice_id="zrHiDhphv9ZnVXBqCLjz",
                model_id="eleven_multilingual_v2"
            )

            # Save the audio file by consuming the generator
            output_path = "output.mp3"
            with open(output_path, "wb") as f:
                for chunk in audio_generator:
                    f.write(chunk)
            
            await websocket.send_json({
                "type": "audio",
                "path": output_path
            })
            logger.info("Audio file path sent to client")
            
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {str(e)}", exc_info=True)
    finally:
        logger.info("WebSocket connection closed")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")