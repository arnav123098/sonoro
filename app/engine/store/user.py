from pathlib import Path
from pydantic import BaseModel, ValidationError

class ProviderConfig(BaseModel):
    base_url: str | None = None
    api_key: str | None = None
    model: str | None = None

class TTSConfig(BaseModel):
    provider: str | None = None

class WebSearchConfig(BaseModel):
    tavily_api_key: str | None = None
    scraper_api_key: str | None = None

class ToolsConfig(BaseModel):
    web_search: WebSearchConfig

class UserConfig(BaseModel):
    llm: ProviderConfig
    stt: ProviderConfig
    tts: TTSConfig
    tools: ToolsConfig

class UserStore:
    def __init__(self, dir: Path):
        self.dir = dir
        self.config: UserConfig = self.get_config()

    def get_config(self) -> UserConfig:
        try:
            with open(self.dir / 'config.json', 'r') as f:
                return UserConfig.model_validate_json(f.read())
        except Exception:
            return UserConfig()

    def write_config(self, config: dict) -> dict:
            try:
                config = UserConfig.model_validate(config)
            except ValidationError as e:
                return {'status': 1, 'message': f'Exception while updating config: {e}', 'config': self.config}

            self.dir.mkdir(parents=True, exist_ok=True)

            with open(self.dir / 'config.json', 'w', encoding='utf-8') as f:
                f.write(config.model_dump_json(indent=2))

            self.config = config

            return {'status': 0, 'message': f'Config saved successfully!', 'config': config}
