import os
import yaml


class ConfigLoader:
    _instance = None

    def __new__(cls, config_path="logic_config.yaml"):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
            cls._instance.config = cls._load_config(config_path)
        return cls._instance

    @staticmethod
    def _load_config(path):
        # Search in current dir, then script dir, then parent
        search_paths = [
            path,
            os.path.join(os.path.dirname(__file__), path),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), path),
        ]

        for p in search_paths:
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        return yaml.safe_load(f)
                except Exception as e:
                    print(f"[!] Warning: Failed to load config {p}: {e}")

        return {"descriptions": {}}

    def get_description(self, key):
        """Retrieve description for a function/block name."""
        return self.config.get("descriptions", {}).get(key, "")

    def get_setting(self, key, default=None):
        return self.config.get("settings", {}).get(key, default)
