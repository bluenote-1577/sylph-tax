import json
from pathlib import Path
from sylph_tax.version import __version__

class JsonConfig:

    def __init__(self, config_location):
        self.config_location = config_location
        self.json = self._load_config(config_location)

        cfg_ver = self.json.get('version', None)
        cfg_ver_major = cfg_ver.split('.')[0]
        version_major = __version__.split('.')[0]

        if cfg_ver_major != version_major:
            print(f"WARNING: Config file version at {self.config_location} is different than sylph-tax version: {cfg_ver} != {__version__} -- sylph-tax has had major updates since the initial run. Check the CHANGELOG to make ensure database compatibility. Update the config file version to {__version__} to suppress this message.")

    def _make_config_dir(self, config_location):
        """Get the config file path."""
        config_dir = Path(config_location)
        config_dir.parent.mkdir(parents=True, exist_ok=True)

    def _load_config(self, config_location) -> dict:
        """Load or create config file."""
        self._make_config_dir(config_location)

        if config_location.exists():
            with open(config_location) as f:
                return json.load(f)

        # Default config
        default_config = {
            'version': __version__,
            'taxonomy_dir': "NONE"
        }

        # Save default config
        with open(config_location, 'w') as f:
            json.dump(default_config, f, indent=2)

        return default_config

    def set_taxonomy_dir(self, path: str) -> None:
        """Set and save custom database directory."""
        abs_path = Path(path).absolute()
        self.json['taxonomy_dir'] = str(abs_path)

        with open(self.config_location, 'w') as f:
            json.dump(self.json, f, indent=2)


