import uvicorn
from connection import BrowserConnection

from data import Data
from web_search import WebSearch
from stt import STT
from llm import LLM
from tts import TTS
from memory import Memory

data = Data()
mem = Memory()

services = dict(
    llm = LLM(memory=mem),
    stt = STT(),
    tts = TTS(),
    tools = {
        'web_search': WebSearch()
    }
)

connection = BrowserConnection(services, data)

if __name__ == "__main__":
    uvicorn.run(
        connection.app,
        host="0.0.0.0",
        port=3000,
        log_level="info",
    )
