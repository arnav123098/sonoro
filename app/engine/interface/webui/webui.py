import socketio
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from interface.webui.movement import Movement

class WebUI:
    def __init__(self, store, services):
        self.sio = services.sio

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
                    allow_origins=["http://localhost:5173", "http://192.168.1.44:5173"],
                    allow_methods=["*"],
                    allow_headers=["*"]
                )
            ]
        )

        self.session = None
        self.services = services
        self.store = store
        self.tool_call = None

        # WALK IN/OUT
        self.mv = Movement(self.sio)
        self.services.tools.make_tool('movement', self.mv) # temporary sloppy fix

        # SONORO HANDLERS
        self.on_from_user = None

        self.ext_sid = None

    async def start(self):
        self.setup_handlers()
        self.services.make_client(self.session.user)

        config = uvicorn.Config(
            self.app,
            host="127.0.0.1",
            port=3000
        )

        server = uvicorn.Server(config)
        self.services.server = server

        print('starting server...')
        print('starting webui...')

        await server.serve()

    async def handle_connect(self, sid, *args):
            print(f'connected {sid}')
    
    async def handle_disconnect(self, sid, *args):
        if not sid == self.ext_sid:
            await self.handle_deselect_character(sid)
        print(f'disconnected {sid}')

    # SONORO HANDLERS AND INTERACTION
    async def from_user(self, sid, data):
        if data['type'] == 'audio' and self.services.stt is not None:
            data['content'] = self.services.stt.stt(data['content']).text
            data['type'] = 'text'
            await self.sio.emit('sttRes', data['content'])

        await self.on_from_user({
            'event_name': 'user_message',
            'content': data
        })

    async def to_ui(self, content):
        if content.get('speak', True) and self.services.tts is not None:
            first = True
            for audio in self.services.tts.tts(content['message'], content.get('expression', 'neutral')):
                await self.sio.emit('playVoice', audio, to=self.mv.char_pos)
                if first:
                    await self.sio.emit('interaction', content)
                    first = False
        else:
            await self.sio.emit('interaction', content)

    async def default_from_char(self, res):
        action, content = res['action'], res['content']

        if action == 'interaction':
            await self.to_ui(content)
        elif action == 'tool_call':
            await self.tool_call(content['tool'], content.get('function'), content.get('args'))
    
    # MENU, CONFIGS AND UTILITIES

    async def handle_get_config(self, sid):
        self.session.user = self.store.user.get_config().model_dump()
        await self.sio.emit('loadConfig', self.session.user, to=sid)

    async def handle_update_config(self, sid, updated_config):
        self.session.user = self.store.user.write_config(updated_config)['config'].model_dump()
        self.services.make_client(self.session.user)

        await self.sio.emit('loadConfig', self.session.user, to=sid)

    async def handle_get_models(self, sid, model_type, config = None):
        service = self.services.llm if model_type == 'llm' else self.services.stt
        service.make_client(config or self.session.user)

        await self.sio.emit('listModels', [service.list_models(), model_type], to=sid)

    async def handle_get_characters(self, sid):
        character_list = {n: self.to_url((f'{n}/images/{p}' if p is not None else f'a-chan/images/pfp.png'), 'characters') for n, p in self.store.characters.list_characters().items()}

        if self.mv.char_conn: # one character at a time
            character_list = {n: p for n, p in character_list.items() if n == self.session.character['name']}

        await self.sio.emit('listCharacters', character_list, to=sid)

    async def handle_get_character_data(self, sid, name, create=False):
        character = self.store.characters.get_character(name, create=create)
        await self.sio.emit('loadCharacterData', character.model_dump(), to=sid)

    async def handle_update_character(self, sid, name, updated_config):
        self.store.characters.write_config(name, updated_config) # TODO: handle toasters

        await self.sio.emit('savedCharacterSuccess', to=sid)

    async def handle_gen_desc(self, sid, data):
        await self.sio.emit('genDesc', self.services.llm.get_character_description(data, self.services.tools.tools['web_search']), to=sid)

    async def handle_select_character(self, sid, name):
        if (self.session.character or {}).get('name') == name:
            await self.sio.emit('selectedCharacter', {
                'name': name,
                'vrm_model': self.to_url(f"{name}/models/{self.session.character['vrm_model']}", 'characters'),
                'theme': self.session.character['theme']
            }, to=sid)
            return
        
        self.session.character = self.store.characters.get_config(name)
        self.mv.reset()

        if self.session.character.theme.chat_background is not None:
            chat_bg = self.to_url(f'{self.session.character.name}/images/{self.session.character.theme.chat_background}', 'characters')
            self.session.character.theme.chat_background = chat_bg

        self.session.character = self.session.character.model_dump()

        self.services.llm.set_character(self.session.character)
        self.services.tts.set_character(self.session.character)

        await self.sio.emit('selectedCharacter', {
            'name': name,
            'vrm_model': self.to_url(f"{name}/models/{self.session.character['vrm_model']}", 'characters'),
            'theme': self.session.character['theme']
        }, to=sid)

    async def handle_movement_setup(self, sid):
        await self.mv.setup(sid)

    async def handle_deselect_character(self, sid):
        self.services.llm.save_mem()
        await self.mv.remove(sid)

    async def handle_walked_out(self, sid, dir):
        await self.mv.manage_char_pos(dir)

    async def handle_delete_character(self, sid, name):
        self.store.characters.delete_character(name)

    async def handle_get_animations(self, sid, *args):
        animations = {
            name: self.to_url(path, 'animations')
            for name, path in self.store.animations.paths.items()
        }

        await self.sio.emit('loadAnimations', {
            'animations': animations,
            'idle_animation': 'idle'
        }, to=sid)

    async def handle_upload_assets(self, sid, character, assets):
        formats = {
            'models': ['vrm'],
            'voicelines': ['wav', 'ogg'],
            'images': ['png' , 'jpg', 'jpeg', 'webp']
        }

        to_upload = []

        for a in assets:
            ext = a['name'].strip().split('.')[-1]
            a_type = None
            for t, f in formats.items():
                if ext in f:
                    a_type = t
                    break

            if a_type is not None:
                to_upload.append({
                    'name': a['name'],
                    'data': a['data'],
                    'type': a_type
                })

        res = self.store.characters.upload_assets(character, to_upload)
        await self.sio.emit('info', res, to=sid)

    async def handle_delete_asset(self, sid, character, asset):
        self.store.characters.delete_asset(character, asset)

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
        self.sio.on('deleteCharacter', self.handle_delete_character)
        self.sio.on('uploadAssets', self.handle_upload_assets)
        self.sio.on('deleteAsset', self.handle_delete_asset)
        self.sio.on('getGenDesc', self.handle_gen_desc)

        # interaction
        self.sio.on('selectCharacter', self.handle_select_character)
        self.sio.on('movementSetup', self.handle_movement_setup)
        self.sio.on('deselectCharacter', self.handle_deselect_character)
        self.sio.on('walkedOut', self.handle_walked_out)
        self.sio.on('getAnimations', self.handle_get_animations)
        self.sio.on('userMessage', self.from_user)
