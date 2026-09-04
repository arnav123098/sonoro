from openai import OpenAI
from io import BytesIO

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

    def list_models(self):
        models = self.client.models.list().data
        return [m.id for m in models if 'whisper' in m.id]

    def stt(self, data):
        audio_file = BytesIO(data)
        audio_file.name = "audio.wav"
        
        transcript = self.client.audio.transcriptions.create(
            model=self.model,
            file=audio_file
        )
        
        return transcript
