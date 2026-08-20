from pathlib import Path
import os
import json

class Data:
    dir = Path.cwd().parent.parent
    characters_dir = dir / 'characters'
    animations_dir = dir / 'animations'
    default_char_dir = (Path.cwd().parent.parent / 'characters/default')

    def __init__(self, asset_paths):
        self.root = Data.dir
        self.config = None
        self.get_config()

        if asset_paths is not None:
            assert 'root' in asset_paths
            self.root = Path(asset_paths['root']).resolve()

            self.characters_dir = Path(asset_paths.get('characters', self.characters_dir)).resolve()
            self.animations_dir = Path(asset_paths.get('animations', self.animations_dir)).resolve()
        else:
            os.makedirs(Data.dir / 'characters', exist_ok=True)
            os.makedirs(Data.dir / 'animations', exist_ok=True)

    def get_config(self):
        try:
            with open(Data.dir / 'config.json', 'r', ) as f:
                config = json.loads(f.read())
        except FileNotFoundError:
            with open(Data.dir / 'config.json', 'x') as f:
                config = {}
                f.write(json.dumps(config))
        except Exception: config = {}

        self.config = config

        return config

    def get_missing_configs(self):
        llm_config = self.config.get('llm', {})
        stt_config = self.config.get('stt', {})
        tts_config = self.config.get('tts', {})
        web_search_config = self.config.get('tools', {}).get('web_search', {})

        missing_configs = [];

        if not all(llm_config.get(k, "") for k in ['base_url', 'api_key']) or not all(stt_config.get(k, "") for k in ['base_url', 'api_key']) or not tts_config.get('provider', ""):
            missing_configs = ['providers', 'models']
        elif not (llm_config.get('model', "") and stt_config.get('model', "")): missing_configs = ['models']
        elif not (all(web_search_config.get(k, "") for k in ['tavily_api_key', 'scraper_api_key'])): missing_configs.append('web_search')
  
        return missing_configs

    def update_config(self, config):
        try:
            with open(Data.dir / 'config.json', 'w') as f:
                f.write(json.dumps(config))
        except FileNotFoundError:
            with open(Data.dir / 'config.json', 'x') as f:
                f.write(config)

        self.config = config

    @staticmethod
    def get_char_config(char_dir_path):
        if not Path.exists(char_dir_path): return # TODO: later add error info on frontend

        if not Path.exists(char_dir_path / 'config.json'):
            config = {
                # 3D
                'model_path': None,
                'model_type': None,

                # Voice
                'expression_to_voice': None, # {expression: voiceline...}

                # Lore
                'name': None,
                'description': None,
                'background_lore': None,

                'pfp': None
            }
        else:
            with open(char_dir_path / 'config.json', 'r') as f:
                config = json.loads(f.read())

            if config['model_path'] is not None and all(not config['model_path'].endswith('.' + fm) for fm in ['vrm', 'gltf']):
                config['model_path'] = None

        return config

    def get_character_dir(self, dirname):
        char_dir_path = self.characters_dir / dirname
        config = Data.get_char_config(char_dir_path)

        os.makedirs(char_dir_path / 'models', exist_ok=True)

        model_paths = [f.name for f in (char_dir_path / 'models').iterdir() if f.is_file() and any(f.name.endswith('.' + fm) for fm in ['vrm', 'gltf'])]

        os.makedirs(char_dir_path / 'pfps', exist_ok=True)

        pfps = [f.name for f in (char_dir_path / 'pfps').iterdir() if f.is_file() and any(f.name.endswith('.' + fm) for fm in ['png', 'jpeg', 'gif', 'jpg'])]

        os.makedirs(char_dir_path / 'voicelines', exist_ok=True)

        voiceline_paths = [f.name for f in (char_dir_path / 'voicelines').iterdir() if f.is_file() and any(f.name.endswith('.' + fm) for fm in ['wav', 'ogg'])]

        data = {
            'config': config,
            'model_paths': model_paths,
            'pfps': pfps,
            'voiceline_paths': voiceline_paths
        }

        return data

    def get_animation_paths(self):
        return {f.name.rstrip('.fbx'): f for f in self.animations_dir.iterdir() if f.is_file() and f.name.endswith('.fbx')}

    def get_all_character_dirs(self):
        dirs = [f.name for f in (self.characters_dir).iterdir() if f.is_dir()]
        path_to_pfp = {
            (self.characters_dir / dirname): Data.get_char_config(self.characters_dir / dirname).get('pfp')
            for dirname in dirs
        }

        default_pfp = f"http://localhost:3000/{(Data.default_char_dir / 'pfps' / 'pfp.png').relative_to(Data.dir).as_posix()}"

        pfps = [
            f"http://localhost:3000/characters/{(path / 'pfps' / pfp).relative_to(self.characters_dir).as_posix()}" if pfp is not None
            else default_pfp
            for path, pfp in path_to_pfp.items()
        ]

        return [{'dir': dir, 'pfp': pfp} for dir, pfp in zip(dirs, pfps)]

    def save_character(self, dirname, config):
        char_dir_path = self.characters_dir / dirname

        try:
            with open(char_dir_path / 'config.json', 'x') as f:
                f.write(json.dumps(config))
        except FileExistsError:
            with open(char_dir_path / 'config.json', 'w') as f:
                f.write(json.dumps(config))
