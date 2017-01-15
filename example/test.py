from mihome.base import XiaomiConnection
from mihome.gateway import Gateway
from mihome.config_manager import YamlConfig

conn = XiaomiConnection()
gateway_data = conn.whois()

gateway = Gateway(
	connection=conn,
	sid=gateway_data['sid'],
	ip=gateway_data['ip'],
	port=gateway_data['port']
)
gateway.register_subdevices()
switch = gateway.connected_devices['switch'][0]

# Listen to switch's events
def switch_cb(item):
	print item
switch.listen(callback=switch_cb)


 ###### Save CONFIG

config = YamlConfig([gateway])
config.save()

###### LOAD CONFIG

config = YamlConfig()
gateways = config.load(conn, Gateway)
for gateway in gateways:
	gateway.register_subdevices()
	print gateway.connected_devices