DEFAULT_SETTINGS = {
    'base_url': 'https://www.bigstash.co/api/v1/',
    'trust_env': False
}


class BigStashAPISettings(object):
    _settings = {
        "default": DEFAULT_SETTINGS
    }

    def __init__(self, profile="default"):
        """
        Initialize the API settings.
        :param profile: optional settings profile name
        """
        self.profile = profile
        if profile is not "default":
            self._settings[profile] = {}

    def __getitem__(self, key):
        return self._settings[self.profile].get(key)

    def __contains__(self, key):
        return key in self._settings[self.profile]

    def __setitem__(self, key, value):
        self._settings[self.profile][key] = value
