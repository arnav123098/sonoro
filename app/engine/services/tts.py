from pocket_tts import TTSModel
import scipy.io.wavfile
import io

class TTS:
    def __init__(self, root):
        self.tts_provider = None
        self.model = None
        self.tts_func = None

        self.exp_to_voice = None
        self.is_tts = False

        self.root = root

    def tts(self, text, expression='neutral'):
        for chunk in self.split_chunks(text):
            yield self.tts_func(chunk, expression)

    def split_chunks(self, text):
        if len(text.split()) <= 13: return [text]
        d = ['.', '?', '!', ';']

        splits = []
        chunk = ''
        for idx, i in enumerate(text):
            chunk += i
            if i in d and (len(chunk.split()) >= 6 or idx == len(text) - 1):
                splits.append(chunk)
                chunk = ''

        return splits
    
    def make_client(self, config):
        if not self.is_tts: return
        self.tts_provider = config.get('tts', {}).get('provider')

        if self.tts_provider == 'Kyutai Pocket TTS':
            self.model = TTSModel.load_model()
            self.tts_func = self.pocket_tts

    def set_character(self, config):
        neutral = config['expression_to_voice']['neutral']
        exp_to_voice = {exp: voice_path or neutral for exp, voice_path in config['expression_to_voice'].items()}

        self.exp_to_voice = {
            exp: (self.root / 'characters' / config['name'] / 'voicelines' / voice_path)
            for exp, voice_path in
            exp_to_voice.items()
        }

    def pocket_tts(self, text, expression='neutral'):
        voice_state = self.model.get_state_for_audio_prompt(
            self.exp_to_voice.get(expression, self.exp_to_voice['neutral'])
        )
        audio = self.model.generate_audio(voice_state, text)

        buffer = io.BytesIO()
        scipy.io.wavfile.write(
            buffer,
            self.model.sample_rate,
            audio.numpy()
        )

        return buffer.getvalue()
