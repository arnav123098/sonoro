from pathlib import Path

class AnimationStore:
    def __init__(self, dir: Path):
        self.dir = dir
        self.paths = {f.stem: f for f in dir.iterdir() if f.is_file() and (f.name.endswith('.fbx') or f.name.endswith('.vrma'))}
