import json
from pathlib import Path
from version import __version__

class JsonConfig:

    def __init__(self):
        self.json = self._load_config()

        cfg_ver = self.json.get('version', None)
        cfg_ver_major = cfg_ver.split('.')[0]
        version_major = __version__.split('.')[0]

        if cfg_ver_major != version_major:
            printerr(f"Config file version at {self._get_config_path()} is different than sylph-tax version: {cfg_ver} != {__version__} -- sylph-tax has had major updates since the initial run. Check the CHANGELOG to make ensure database compatibility. Update the config file version to {__version__} to suppress this message.")

    def _get_config_path(self) -> Path:
        """Get the config file path."""
        config_dir = Path.home() / '.config' / 'sylph-tax'
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / 'config.json'

    def _load_config(self) -> dict:
        """Load or create config file."""
        config_path = self._get_config_path()

        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)

        # Default config
        default_config = {
            'version': __version__,
            'taxonomy_dir': "NONE"
        }

        # Save default config
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)

        return default_config

    def set_taxonomy_dir(self, path: str) -> None:
        """Set and save custom database directory."""
        path = Path(path).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        self.json['taxonomy_dir'] = str(path)

        with open(self._get_config_path(), 'w') as f:
            json.dump(self.json, f, indent=2)


