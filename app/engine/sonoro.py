from services.stt import STT
from services.llm import LLM
from services.tts import TTS

from tools.web_search import WebSearch
from tools.music_player import MusicPlayer

from store.store import Store
from memory import Memory

from interface.webui import WebUI
from interface.tui import TUI

class Services():
    def __init__(self, llm, stt, tts):
        self.llm = llm
        self.stt = stt
        self.tts = tts
        self.dict = {
            'llm': llm,
            'stt': stt,
            'tts': tts
        }

class Sonoro:
    def __init__(self, root: str, use_memory: bool = True, asset_paths: dict | None = None):
        self.store = Store(root, asset_paths)
        self.memory = Memory() if use_memory else None

        self.services = Services(
            llm = LLM(memory=self.memory),
            stt = STT(),
            tts = TTS(self.store.root)
        )

        self.tools = {
            'web_search': WebSearch(),
            'music_player': MusicPlayer()
        }

        self.interface = None

    def make_interface(self, interface_type):
        if interface_type not in ('webui', 'tui'):
            raise ValueError(f"Unknown interface type: {interface_type}. Interface types include: webui, tui")

        if interface_type == 'webui':
            self.services.tts.is_tts = True
            self.services.llm.make_context(interface_type='webui', animation_paths=self.store.animations.paths)
            self.interface = WebUI(self.store, self.services, self.tools, self.make_client)
        else:
            self.services.llm.make_context(interface_type='tui', animation_paths=self.store.animations.paths)
            self.interface = TUI(self.store, self.services, self.tools, self.make_client)

    def make_client(self, config):
        for service in self.services.dict.values():
            service.make_client(config)

        for tool in self.tools.values():
            if hasattr(tool, 'make_client'):
                tool.make_client(config)

    def cleanup(self):
        for service in self.services.dict.values():
            if hasattr(service, 'cleanup'):
                service.cleanup()
        
        for tool in self.tools.values():
            if hasattr(tool, 'cleanup'):
                tool.cleanup()

if __name__ == "__main__":
    sonoro = Sonoro('../../')

    ui = {
        1: 'tui',
        2: 'webui'
    }
    print('\n'.join([f'{i}. {u}' for i, u in ui.items()]))

    ui_type = ui.get(int(input('Interface type: ')))

    sonoro.make_interface(ui_type)

    try:
        sonoro.interface.start()
    finally:
        sonoro.cleanup()

# one last piece: add delete character option
