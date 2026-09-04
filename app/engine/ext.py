class Ext:
    def __init__(self, sonoro):
        self.sonoro = sonoro
        self.setup_handlers()

    async def setup_ext(self, sid):
        self.sonoro.interface.ext_sid = sid

    async def to_ext(self, event_type, event):
        await self.sonoro.sio.emit(event_type, event)

    async def set_on_from_user(self, *args):
        self.sonoro.interface.on_from_user = self.sonoro.from_user_to_ext

    async def set_on_from_char(self, *args):
        self.sonoro.on_from_char = self.sonoro.from_char_to_ext

    async def set_on_tool_res(self, *args):
        self.sonoro.on_tool_res = self.sonoro.tool_res_to_ext

    async def to_ui(self, sid, content):
        if self.sonoro.interface_type == 'webui':
            await self.sonoro.interface.to_ui(content)
        else:
            self.sonoro.interface.to_ui(content)

    async def use_stt(self, sid, data):
        await self.sonoro.sio.emit('task_res', (data['task_id'], self.sonoro.services.stt.stt(data['args'])), to=sid)

    async def use_tts(self, sid, data):
        await self.sonoro.sio.emit('task_res', (data['task_id'], self.sonoro.services.tts.tts(data['args']['text'], data['args']['expression'])), to=sid)

    async def use_llm(self, sid, data):
        await self.sonoro.sio.emit('task_res', (data['task_id'], self.sonoro.services.llm.use_llm(data['args'])), to=sid)

    async def get_character_response(self, sid, data):
        await self.sonoro.sio.emit('task_res', (data['task_id'], self.sonoro.services.llm.get_response(data['args'])), to=sid)

    def setup_handlers(self):
        self.sonoro.sio.on('setup', self.setup_ext)
        self.sonoro.sio.on('set_on_from_user', self.set_on_from_user)
        self.sonoro.sio.on('set_on_from_char', self.set_on_from_char)
        self.sonoro.sio.on('set_on_tool_res', self.set_on_tool_res)

        self.sonoro.sio.on('to_ui', self.to_ui)
        self.sonoro.sio.on('use_stt', self.use_stt)
        self.sonoro.sio.on('use_tts', self.use_tts)
        self.sonoro.sio.on('get_character_response', self.get_character_response)
