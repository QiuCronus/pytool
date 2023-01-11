import abc
import configparser

try:
    import yaml
except ImportError:
    yaml = None

TRUE = (True, "true", "True", "on", "yes", "Yes")
FALSE = (False, "false", "False", "off", "no", "No")


class Config(object):
    def __init__(self, path):
        self._configure = {}
        self.load(path)

    @abc.abstractmethod
    def load(self, path):
        raise NotImplementedError

    def get(self, key, default=None):
        def _gets(_container: dict, _path: str):
            _path = _path.strip()
            if _path.count(".") > 0:
                pre, ext = _path.split(".", 1)
                if pre in _container.keys():
                    return _gets(_container[pre], ext)
            if _path in _container.keys():
                return _container.get(_path)
            return default

        return _gets(self._configure, key)


class IniConfig(Config):
    def load(self, path):
        cfg = configparser.ConfigParser()
        if not cfg.read(path):
            raise RuntimeError("load failed.")
        self._configure.clear()
        for section in cfg.sections():
            self._configure[section] = {}
            for option in cfg.options(section):
                value = cfg.get(section, option)
                value = value.strip(" ").strip("\n")
                if "\n" in value:
                    value = value.split("\n")
                self._configure[section][option] = value

if yaml:
    class YamlConfig(Config):
        def load(self, path):
            with open(path, "r") as fd:
                self._configure = yaml.safe_load(fd)