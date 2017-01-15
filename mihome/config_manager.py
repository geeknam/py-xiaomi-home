import yaml
import json
import os

XIAOMI_CONFIG_FILE_PATH = os.environ.get('XIAOMI_CONFIG_FILE_PATH', '.')
XIAOMI_CONFIG_NAME = os.environ.get('XIAOMI_CONFIG_NAME', 'xiaomi-config')

class BaseConfig(object):

	def __init__(self, gateways=None):
		self.gateways = gateways or []

	def serialise(self):
		return {
			'xiaomi_devices': [
				gateway.serialise()
				for gateway in self.gateways
			]
		}

	def format(self):
		raise NotImplementedError

	@property
	def config_file(self):
		file_name = '%s.%s' % (XIAOMI_CONFIG_NAME, self.file_extension)
		return os.path.join(XIAOMI_CONFIG_FILE_PATH, file_name)

	def save(self):
		config_file = open(self.config_file, 'wb')
		config_file.write(self.format())
		config_file.close()

	def load(self, connection, device_class):
		config_file = open(self.config_file, 'rb')
		content = config_file.read()
		return device_class.deserialise(
			connection=connection,
			data=self.to_dict(content)['xiaomi_devices']
		)


class YamlConfig(BaseConfig):

	file_extension = 'yml'

	def format(self):
		return yaml.safe_dump(
			self.serialise(), default_flow_style=False,
			indent=4
		)

	def to_dict(self, content):
		return yaml.load(content)


class JsonConfig(BaseConfig):

	file_extension = 'json'

	def format(self):
		return json.dumps(self.serialise(), indent=4)

	def to_dict(self, content):
		return json.loads(content)