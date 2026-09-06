from services.services import Services
from services.tools import Tools

from interface.webui.webui import WebUI
from interface.tui import TUI

from store.characters import CharacterConfig

from store.store import Store
from memory import Memory

from ext import Ext

from dataclasses import dataclass
from typing import Callable
import inspect
import socketio
import asyncio
import uvicorn

@dataclass
class SessionData:
    user: dict
    user_ready: bool
    update_user: Callable
    character: CharacterConfig | None = None

class Sonoro:
    def __init__(self, root: str, *, asset_paths: dict | None = None, use_memory: bool = True):
        self.store = Store(root, asset_paths)
        self.memory = Memory() if use_memory else None

        self.sio = socketio.AsyncServer(
            async_mode='asgi',
            cors_allowed_origins='*',
            max_http_buffer_size=8*1024*1024
        )

        self.server = None # uvicorn

        self.services = Services(
            llm = None,
            stt = None,
            tts = None,
            tools = Tools(),
            sio = self.sio,
            server = self.server
        )

        self.interface = None
        self.interface_type = None
        self.session = None

        self.on_tool_res = None
        self.on_from_char = None # or send_to_sdk_side

        self.ext = Ext(self)

    def check_user_config(self, config):
        user_ready = True

        # LLM, STT, TTS
        for provider in (config.llm, config.stt, config.tts):
            if not all(value for value in provider.model_dump().values()):
                user_ready = False
                break

        # Web search
        if not all(config.tools.web_search.model_dump().values()): # a quick brute force solution even though it's sloppy (meow)
            if 'web_search' not in self.services.tools.unready:
                self.services.tools.unready.append('web_search')
        else:
            if 'web_search' in self.services.tools.unready:
                self.services.tools.unready.remove('web_search')

        return user_ready

    def session_update_user(self):
        config = self.store.user.get_config()
        self.session.user = config.model_dump()
        self.session.user_ready = self.check_user_config(config)

    def make_interface(self, interface_type):
        if interface_type not in ('webui', 'tui'):
            raise ValueError(f"Unknown interface type: {interface_type}. Interface types include: webui, tui")

        self.interface_type = interface_type

        if interface_type == 'webui':
            if self.services.tts is not None:
                self.services.tts.is_tts = True

            if self.services.llm is not None:
                self.services.llm.make_context(interface_type='webui', animation_paths=self.store.animations.paths)

            self.interface = WebUI(self.store, self.services)
        else:
            if self.services.llm is not None:
                self.services.llm.make_context(interface_type='tui', animation_paths=self.store.animations.paths)
            
            self.interface = TUI(self.store, self.services)

    async def start(self):
        config = self.store.user.get_config()
        self.session = SessionData(
            user = config.model_dump(),
            user_ready = self.check_user_config(config),
            update_user = self.session_update_user
        )

        self.interface.session = self.session
        self.interface.tool_call = self.tool_call

        if self.interface_type == 'webui':
            await self.interface.start()
        else:
            await asyncio.gather(
                self.run_server(),
                asyncio.to_thread(self.interface.start)
            )

    async def run_server(self):
        socket_app = socketio.ASGIApp(self.sio)

        config = uvicorn.Config(
            socket_app,
            host="127.0.0.1",
            port=3000,
            log_config=None
        )

        self.server = uvicorn.Server(config)
        self.services.server = self.server

        print('starting server...')
        await self.server.serve()

    def set_default_services(self):
        from services.stt import STT
        from services.llm import LLM
        from services.tts import TTS

        self.services.llm = LLM(memory=self.memory)
        self.services.stt = STT()
        self.services.tts = TTS(self.store.root)

    def set_default_handlers(self):
        self.interface.on_from_user = self.default_from_user
        self.on_from_char = self.interface.default_from_char
        self.on_tool_res = self.default_tool_res_handler

    async def from_user_to_ext(self, event):
        await self.ext.to_ext('from_user', event)

    async def from_char_to_ext(self, event):
        await self.ext.to_ext('from_char', event)

    async def tool_res_to_ext(self, res):
        await self.ext.to_ext('tool_res', res)

    async def default_from_user(self, event):
        if self.services.llm is None:
            print('No LLM found (attempted to call default_from_user)')
            return

        d_type = event['content']['type']
        if d_type != 'text':
            print(f'from_user event data type should be text and not {d_type}')
            return
        
        del event['content']['type']
        res = self.services.llm.get_response(event)
        await self.from_char(res)

    async def default_tool_res_handler(self, res):
        await self.from_char(self.services.llm.get_response(res))

    async def tool_call(self, tool_name, func, args):
        tool_call_res = await self.services.tools.call(tool_name, func, args)

        print('[tool_call_done] ', tool_call_res['event_name'])
        # print('received tool_call res: ', tool_call_res)
        
        await self.on_tool_res(tool_call_res)

    async def from_char(self, res):
        res = self.on_from_char(res) # default or send to sdk side via sio
        if inspect.isawaitable(res): await res

    def cleanup(self): self.services.cleanup()
