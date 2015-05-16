import os
import json
import collections

DEFAULT_SETTINGS = {
    'base_url': 'https://www.bigstash.co/api/',
    'trust_env': False,
    'verify': True,
    'log_level': 'ERROR'
}

DEFAULT_CONFIG_ROOT = os.path.expanduser(
    os.path.join('~', '.config', 'bigstash'))


class BigStashAPISettings(collections.MutableMapping):
    _settings = {
        "default": DEFAULT_SETTINGS
    }

    def __init__(self, profile=None, root=None):
        """
        Initialize the API settings.
        :param profile: optional settings profile name
        """
        if profile is None:
            profile = os.environ.get('BS_PROFILE', 'default')
        self.profile = profile
        if profile != "default":
            self._settings[profile] = DEFAULT_SETTINGS
        self.config_root = root or os.environ.get(
            'BS_CONFIG_ROOT', DEFAULT_CONFIG_ROOT)
        if 'BS_API_URL' in os.environ:
            self['base_url'] = os.environ['BS_API_URL']
        self['log_level'] = os.environ.get("BS_LOG_LEVEL", "error").upper()

    @property
    def _current_settings(self):
        return self._settings[self.profile]

    def __getitem__(self, key):
        return self._current_settings.get(key)

    def __delitem__(self, key):
        del self._current_settings[key]

    def __contains__(self, key):
        return key in self._current_settings

    def __setitem__(self, key, value):
        self._current_settings[key] = value

    def __iter__(self):
        return iter(self._current_settings)

    def __len__(self):
        return len(self._current_settings)

    @classmethod
    def load_settings(cls, profile=None, path=None):
        obj = cls(profile)
        path = path or obj.get_config_file('profiles')
        if not os.path.exists(path):
            return obj
        with open(path or obj.get_config_file('profiles')) as f:
            profiles = json.load(f)
            obj.update(profiles.get(obj.profile, {}))
            return obj

    def get_config_file(self, path):
        return os.path.join(self.config_root, path)

    def read_config_file(self, path):
        with open(self.get_config_file(path)) as f:
            return json.load(f)

    def write_config_file(self, path, data):
        if not os.path.exists(self.config_root):
            os.makedirs(self.config_root)
        with open(os.path.join(self.config_root, path), 'w') as f:
            json.dump(data, f)
