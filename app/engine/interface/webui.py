import socketio
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

import inspect
from io import BytesIO

class WebUI:
    def __init__(self, store, services, tools, make_client):
        self.sio = socketio.AsyncServer(
            async_mode='asgi',
            cors_allowed_origins='*',
            max_http_buffer_size=8*1024*1024
        )

        socket_app = socketio.ASGIApp(self.sio)
        self.app = Starlette(
            routes=[
                Mount("/characters", app=StaticFiles(directory=(store.character_dir))),
                Mount("/animations", app=StaticFiles(directory=(store.animation_dir))),
                Mount("/", app=socket_app)
            ],
            middleware=[
                Middleware(
                    CORSMiddleware,
                    allow_origins=["http://localhost:5173"],
                    allow_methods=["*"],
                    allow_headers=["*"]
                )
            ]
        )

        self.services = services
        self.tools = tools
        self.store = store
        self.make_client = make_client

        self.config = None
        
        self.character = None
        self.locked = False # only one character

    def start(self):
        self.setup_handlers()
        self.make_client(self.store.user.get_config().model_dump())

        uvicorn.run(
            self.app,
            host="0.0.0.0",
            port=3000,
            log_level="info",
        )

    async def handle_user_message(self, sid, data):
        if data['type'] == 'audio':
            audio_file = BytesIO(data['content'])
            audio_file.name = "audio.wav"

            content = self.services.stt.stt(audio_file).text
            await self.sio.emit('sttRes', content)
        else:
            content = data['content']
        
        res = self.services.llm.get_response({
            'event_name': 'user_message',
            'content': content
        })

        await self.from_char(res, sid)

    async def from_char(self, res, sid):
        action, content = res['action'], res['content']

        if action == 'tool_call':
            tool_name, function, args = content.get('tool'), content.get('function'), content.get('args')

            tool_obj = self.tools.get(tool_name)
            if tool_obj is not None:
                fn = getattr(tool_obj, function, None)
            else:
                fn = None

            if fn is not None:
                tool_call_res = fn(**args)

            if inspect.isawaitable(tool_call_res): tool_call_res = await tool_call_res

            print('tool_call_done: ', tool_call_res['event_name'])
            # print('received tool_call res: ', tool_call_res)
                    
            await self.from_char(self.services.llm.get_response(tool_call_res)) # send result to llm

        if action == 'interaction':
            if content.get('speak', True):
                audio = self.services.tts.tts(content['message'], content.get('expression', 'neutral'))
                content['audio'] = audio

            await self.sio.emit('interaction', content, to=sid)

    async def handle_get_config(self, sid):
        self.config = self.store.user.get_config().model_dump()
        await self.sio.emit('loadConfig', self.config, to=sid)

    async def handle_update_config(self, sid, updated_config):
        self.config = self.store.user.write_config(updated_config)['config'].model_dump()
        self.make_client(self.config)
        await self.sio.emit('loadConfig', self.config, to=sid)

    async def handle_get_models(self, sid, *args):
        self.services.llm.make_client(self.config)
        self.services.stt.make_client(self.config)

        llm, stt = self.services.llm.client.models.list(), self.services.stt.client.models.list()
        model_list = {
            'llm': [m.id for m in llm.data if 'whisper' not in m.id],
            'stt': [m.id for m in stt.data if 'whisper' in m.id]
        }

        await self.sio.emit('listModels', model_list, to=sid)

    async def handle_get_characters(self, sid):
        character_list = {n: self.to_url((f'{n}/images/{p}' if p is not None else f'a-chan/images/pfp.png'), 'characters') for n, p in self.store.characters.list_characters().items()}

        await self.sio.emit('listCharacters', character_list, to=sid)

    async def handle_get_character_data(self, sid, name, create=False):
        await self.sio.emit('loadCharacterData', self.store.characters.get_character(name, create=create).model_dump(), to=sid)

    async def handle_update_character(self, sid, name, updated_config):
        self.store.characters.write_config(name, updated_config) # TODO: handle toasters

        await self.sio.emit('savedCharacterSuccess', to=sid)

    async def handle_gen_desc(self, sid, data):
        await self.sio.emit('genDesc', self.services.llm.get_character_description(data, self.tools['web_search']), to=sid)

    async def handle_select_character(self, sid, name):
        self.character = self.store.characters.get_config(name).model_dump()

        self.services.llm.set_character(self.character)
        self.services.tts.set_character(self.character)

        model_dir = self.store.character_dir / name / 'models'
        rel = (model_dir / self.character['vrm_model']).relative_to(model_dir)
        url = f"http://localhost:3000/characters/{name}/models/{rel.as_posix()}"

        await self.sio.emit('selectedCharacter', {
            'name': name,
            'vrm_model': url,
            'theme': self.character['theme']
        }, to=sid)

    async def handle_get_animations(self, sid, *args):
        animations = {}
        for name, path in self.store.animations.paths.items():
            rel = path.relative_to(self.store.root)
            url = f"http://localhost:3000/{rel.as_posix()}"

            animations[name] = url

        await self.sio.emit('loadAnimations', {
            'animations': animations,
            'idle_animation': 'idle'
        }, to=sid)

    async def handle_connect(self, sid, *args):
        print(f'connected {sid}')
    
    async def handle_disconnect(self, sid, *args):
        self.services.llm.save_mem()
        print(f'disconnected {sid}')

    def to_url(self, path, store):
        dir = {
            'characters': self.store.character_dir,
            'animations': self.store.animation_dir
        }

        rel = (dir[store] / path).relative_to(dir[store])
        return f"http://localhost:3000/{store}/{rel.as_posix()}"

    def setup_handlers(self):
        # connection
        self.sio.on('connect', self.handle_connect)
        self.sio.on('disconnect', self.handle_disconnect)

        # user/global
        self.sio.on('getConfig', self.handle_get_config)
        self.sio.on('updateConfig', self.handle_update_config)
        self.sio.on('getModels', self.handle_get_models)

        # characters
        self.sio.on('getCharacters', self.handle_get_characters)
        self.sio.on('getCharacterData', self.handle_get_character_data)
        self.sio.on('updateCharacter', self.handle_update_character)
        self.sio.on('getGenDesc', self.handle_gen_desc)

        # interaction
        self.sio.on('selectCharacter', self.handle_select_character)
        self.sio.on('getAnimations', self.handle_get_animations)
        self.sio.on('userMessage', self.handle_user_message)
