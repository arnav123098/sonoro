class Services():
    def __init__(self, llm, stt, tts, tools, sio, server):
        self.llm = llm
        self.stt = stt
        self.tts = tts
        self.tools = tools
        self.sio = sio
        self.server = server
        
        self.dict = lambda: {
            'llm': self.llm,
            'stt': self.stt,
            'tts': self.tts,
            'tools': self.tools
        }

    def make_client(self, config):
        for service in self.dict().values():
            if hasattr(service, 'make_client'):
                service.make_client(config)

    def cleanup(self):
        for service in self.dict().values():
            if hasattr(service, 'cleanup'):
                service.cleanup()
