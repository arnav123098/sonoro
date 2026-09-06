import shutil
from pathlib import Path
from pydantic import BaseModel, ValidationError

class ThemeConfig(BaseModel):
    chat_background: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None

class ExpToVoiceConfig(BaseModel):
    neutral: str | None = None
    happy: str | None = None
    sad: str | None = None
    angry: str | None = None
    embarrassed: str | None = None
    excited: str | None = None

class CharacterConfig(BaseModel):
    name: str
    description: str | None = None
    background_lore: str | None = None
    convo_examples: list[list] | None = None

    pfp: str | None = None
    theme: ThemeConfig  = ThemeConfig()

    vrm_model: str | None = None

    expression_to_voice: ExpToVoiceConfig = ExpToVoiceConfig()

class Character(BaseModel):
    name: str
    config: CharacterConfig
    vrm_models: list
    images: list
    voicelines: list

class CharacterStore:
    def __init__(self, dir: Path):
        self.dir = dir

    def list_characters(self) -> dict:
        return {
            name: self.get_config(name).model_dump().get('pfp')
            for name in
            [f.name for f in (self.dir).iterdir() if f.is_dir()]
        } # {name: pfp...}

    def get_character(self, name: str, create: bool = False) -> Character | None:
        char_dir = self.dir / name

        if not (create or char_dir.exists()) or (create and char_dir.exists()): return

        if create: char_dir.mkdir(parents=True, exist_ok=True)

        config = self.get_config(name)

        (char_dir / 'models').mkdir(parents=True, exist_ok=True)
        (char_dir / 'images').mkdir(parents=True, exist_ok=True)
        (char_dir / 'voicelines').mkdir(parents=True, exist_ok=True)

        vrm_models = [f.name for f in (char_dir / 'models').iterdir() if f.is_file() and f.name.endswith('.vrm')]

        images = [f.name for f in (char_dir / 'images').iterdir() if f.is_file() and any(f.name.endswith(f'.{fm}') for fm in ['png', 'jpeg', 'gif', 'jpg'])]

        voicelines = [f.name for f in (char_dir / 'voicelines').iterdir() if f.is_file() and any(f.name.endswith('.' + fm) for fm in ['wav', 'ogg'])]

        return Character.model_validate({
            'name': name,
            'config': config,
            'vrm_models': vrm_models,
            'images': images,
            'voicelines': voicelines
        })
        
    def get_config(self, name: str) -> CharacterConfig:
        char_dir = self.dir / name

        try:
            with open(char_dir / 'config.json', 'r') as f:
                return CharacterConfig.model_validate_json(f.read())
        except Exception:
            return CharacterConfig.model_validate({'name': name})

    def write_config(self, name: str, config: dict) -> dict:
            char_dir = self.dir / name

            if config['name'] != name:
                char_dir = char_dir.rename(self.dir / config['name'])

            try:
                config = CharacterConfig.model_validate(config)
            except ValidationError as e:
                return {'status': 1, 'message': f'Exception while updating character settings: {e}'}

            char_dir.mkdir(parents=True, exist_ok=True)

            with open(char_dir / 'config.json', 'w', encoding='utf-8') as f:
                f.write(config.model_dump_json(indent=2))

            return {'status': 0, 'message': f'Character saved successfully!'}

    def delete_character(self, name: str):
        path = self.dir / name
        shutil.rmtree(path)
    
    def upload_assets(self, name: str, assets: list[dict]) -> dict:
        char_path = self.dir / name

        for a in assets: (char_path / a['type'] / a['name']).write_bytes(a['data'])

        return {'status': 0, 'message': f'{len(assets)} Files uploaded successfully!'}

    def delete_asset(self, name: str, asset: dict):
        path = self.dir / name / asset['type'] / asset['name']
        path.unlink(missing_ok=True)
