import yaml
import os

DEFAULT_POWER = 1000
DEFAULT_POWER_REQUIRED = 2000
DEFAULT_TEMPERATURE_CONSTANT = 4.0

class RadiatorConfig:
    def __init__(self, power=DEFAULT_POWER, included=True):
        self.power = power
        self.included = included

    def to_dict(self):
        return {
            'power': self.power,
            'included': self.included
        }

    @staticmethod
    def from_dict(data):
        return RadiatorConfig(
            power=data.get('power', DEFAULT_POWER),
            included=data.get('included', True)
        )

class Config:
    def __init__(self, temperature_constant=DEFAULT_TEMPERATURE_CONSTANT, power_required=DEFAULT_POWER_REQUIRED, radiators=None):
        self.temperature_constant = temperature_constant
        self.power_required = power_required
        self.radiators = radiators if radiators is not None else {} 

    def to_dict(self):
        return {
            'temperature_constant': self.temperature_constant,
            'power_required': self.power_required,
            'radiators': {name: radiator.to_dict() for name, radiator in self.radiators.items()}
        }

    @staticmethod
    def from_dict(data):
        radiators = {name: RadiatorConfig.from_dict(radiator) for name, radiator in data.get('radiators', {}).items()}
        return Config(
            temperature_constant=data.get('temperature_constant', DEFAULT_TEMPERATURE_CONSTANT),
            power_required=data.get('power_required', DEFAULT_POWER_REQUIRED),
            radiators=radiators
        )

class ConfigLoader:
    _config = Config()
    _path = "config.yaml"

    @staticmethod
    def load():
        if not os.path.exists(ConfigLoader._path):
            ConfigLoader.save()
        with open(ConfigLoader._path, 'r') as file:
            data = yaml.safe_load(file)
            ConfigLoader._config = Config.from_dict(data)

    @staticmethod
    def save():
        with open(ConfigLoader._path, 'w') as file:
            yaml.safe_dump(ConfigLoader._config.to_dict(), file)

