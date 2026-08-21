from store.user import UserStore
from store.characters import CharacterStore
from store.animations import AnimationStore

from pathlib import Path

class Store:
    def __init__(
        self,
        root: str,
        asset_paths: dict[str, str] | None = None
    ):
        self.root = Path(root).resolve()

        if asset_paths is not None:
            self.character_dir = Path(asset_paths['characters']).resolve()
            self.animation_dir = Path(asset_paths['animations']).resolve()
        else:
            self.character_dir = self.root / 'characters'
            self.animation_dir = self.root / 'animations'

        self.user = UserStore(self.root)
        self.characters = CharacterStore(self.character_dir)
        self.animations = AnimationStore(self.animation_dir)
