from pocket_tts import TTSModel
from gradio_client import Client, handle_file
import scipy.io.wavfile
import io
from data import Data

class TTS:
    def __init__(self):
        self.tts_provider = None
        self.model = None
        self.tts = None

        self.exp_to_voice = None

    def make_client(self, config):
        self.tts_provider = config.get('tts', {}).get('provider')

        if self.tts_provider == 'Kyutai Pocket TTS':
            self.model = TTSModel.load_model()
            self.tts = self.pocket_tts
        elif self.tts_provider == 'F5 TTS (Gradio)':
            self.model = Client("http://127.0.0.1:7860") # TODO: fix install; fix latency in colab
            self.tts = self.f5_tts

    def set_character(self, config):
        neutral = config['expression_to_voice']['neutral']
        exp_to_voice = {exp: voice_path or neutral for exp, voice_path in config['expression_to_voice'].items()}

        self.exp_to_voice = {
            exp: (Data.dir / 'characters' / config['dir'] / 'voicelines' / voice_path)
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

    def f5_tts(self, text, expression='neutral'):
            ref = self.exp_to_voice.get(expression, self.exp_to_voice['neutral']) # not completed; later this will be a tuple (path, ref_text)

            result = self.model.predict(
                ref_audio_input=handle_file(ref[0]),
                ref_text_input=ref[1],
                gen_text_input=text,
                remove_silence=False,
                randomize_seed=True,
                seed_input=0,
                cross_fade_duration_slider=0.15,
                nfe_slider=32,
                speed_slider=0.85,
                api_name="/basic_tts",
            )

            audio_path = result[0]

            with open(audio_path, "rb") as f:
                audio_bytes = f.read()

            return audio_bytes
