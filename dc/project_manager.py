from pathlib import Path
import json

class project_manager:
    def __init__(self):
        root_path = Path(__file__).resolve().parent.parent
        target_path = root_path/"project_config"
        target_path = Path(target_path)
        if target_path.is_dir():
            self.projects = target_path.iterdir()
