from openai import OpenAI

class STT:
    def __init__(self):
        self.client = None
        self.model = None

    def make_client(self, config):
        stt_config = config.get('stt', {})
        base_url, api_key, model = stt_config.get('base_url'), stt_config.get('api_key'), stt_config.get('model')

        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        ) if base_url and api_key else None
        
        self.model = model if model and self.client else None

    def stt(self, data):
        transcript = self.client.audio.transcriptions.create(
            model=self.model,
            file=data
        )
        
        return transcript
