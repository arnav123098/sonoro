import socketio
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

import inspect
from io import BytesIO

class BrowserConnection:
    def __init__(self, services, data):
        self.sio = socketio.AsyncServer(
            async_mode='asgi',
            cors_allowed_origins='*',
            max_http_buffer_size=8*1024*1024
        )

        socket_app = socketio.ASGIApp(self.sio)

        self.app = Starlette(
            routes=[
                Mount("/characters", app=StaticFiles(directory=(data.dir / 'characters'))),
                Mount("/animations", app=StaticFiles(directory=(data.dir / 'animations'))),
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
        self.llm = services['llm']
        self.stt = services['stt']
        self.tts = services['tts']
        self.tools = services['tools']

        self.data = data

        self.make_client(data.config)

        self.sio.on('connect', self.handle_connect)
        self.sio.on('disconnect', self.handle_disconnect)
        self.sio.on('getConfig', self.handle_get_config)
        self.sio.on('updateConfig', self.handle_update_config)
        self.sio.on('getModels', self.handle_get_models)

        self.sio.on('getCharacters', self.handle_get_characters)
        self.sio.on('getCharacterData', self.handle_get_character_data)
        self.sio.on('saveCharacter', self.handle_save_character)
        self.sio.on('selectCharacter', self.handle_select_character)
        self.sio.on('getGenDesc', self.handle_gen_desc)

        self.sio.on('getAnimations', self.handle_get_animations)
        self.sio.on('userMessage', self.handle_user_message)

    def make_client(self, config):
        for service in self.services.values():
            if type(service) == dict:
                for s in service.values(): s.make_client(config)
            else: service.make_client(config)

    async def handle_connect(self, sid, *args):
        self.data.config = self.data.get_config()
        print('connected')

    async def handle_disconnect(self, sid, *args):
        self.llm.save_mem()
        print('disconnected')

    async def handle_get_config(self, *args):
        await self.sio.emit('loadConfig', {'config': self.data.config, 'missing_configs': self.data.get_missing_configs()})

    async def handle_update_config(self, sid, updated_config):
        self.data.update_config(updated_config)

        self.make_client(self.data.config)

        await self.handle_get_config()

    async def handle_get_models(self, *args):
        self.llm.make_client(self.data.config)
        self.stt.make_client(self.data.config)

        llm, stt = self.llm.client.models.list(), self.stt.client.models.list()
        model_list = {
            'llm': [m.id for m in llm.data if 'whisper' not in m.id],
            'stt': [m.id for m in stt.data if 'whisper' in m.id]
        }

        await self.sio.emit('listModels', model_list)
        
    async def handle_get_characters(self, sid):
        await self.sio.emit('listCharacters', self.data.get_all_character_dirs())

    async def handle_get_character_data(self, sid, dir):
        await self.sio.emit('loadCharacterData', self.data.get_character_dir(dir))

    async def handle_save_character(self, sid, char_data):
        self.data.save_character(char_data['dir'], char_data['config'])

        await self.sio.emit('savedCharacterSuccess')

    async def handle_select_character(self, sid, dir):
        config = self.data.get_character_dir(dir)['config']

        config['dir'] = dir # used for path related things

        self.llm.set_character(config)
        self.tts.set_character(config)

        rel = (self.data.dir / config["model_path"]).relative_to(self.data.dir)
        url = f"http://localhost:3000/characters/{dir}/models/{rel.as_posix()}"

        await self.sio.emit('selectedCharacter', {'name': config['name'], 'model_path': url, 'model_type': config['model_type']})

    async def handle_get_animations(self, *args):
        animations = {}
        for name, path in self.data.get_animation_paths().items():
            rel = path.relative_to(self.data.dir)
            url = f"http://localhost:3000/{rel.as_posix()}"

            animations[name] = url

        await self.sio.emit('loadAnimations', {
            'animations': animations,
            'idle_animation': 'idle'
        })

    async def handle_gen_desc(self, sid, data):
        await self.sio.emit('genDesc', self.llm.get_character_description(data, self.tools['web_search']))

    async def handle_user_message(self, sid, data):
        if data['type'] == 'audio':
            audio_file = BytesIO(data['content'])
            audio_file.name = "audio.wav"

            content = self.stt.stt(audio_file).text
            await self.sio.emit('sttRes', content)
        else:
            content = data['content']
        
        res = self.llm.get_response({
            'event_name': 'user_message',
            'content': content
        })

        await self.from_char(res)

    async def from_char(self, res):
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
                    
            await self.from_char(self.llm.get_response(tool_call_res)) # send result to llm

        if action == 'interaction':
            if content.get('speak', True):
                audio = self.tts.tts(content['message'], content.get('expression', 'neutral'))
                content['audio'] = audio

            await self.sio.emit('interaction', content)
