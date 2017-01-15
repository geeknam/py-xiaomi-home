xiaomi-home
==================

Pythonic bindings for Xiaomi Smart Home suite


Basic Usage
==================


Discover gateways and subdevices by sending `read` commands.

```python
from mihome.base import XiaomiConnection
from mihome.gateway import Gateway

conn = XiaomiConnection()
gateway_data = conn.whois()

gateway = Gateway(
	connection=conn,
	sid=gateway_data['sid'],
	ip=gateway_data['ip'],
	port=gateway_data['port']
)
gateway.register_subdevices()
```

Listen to any devices events

```python
def switch_cb(item):
	# publish to mqtt / kafka / redis
	print item

for switch in gateway.connected_devices['switch']:
	switch.listen(callback=switch_cb)
```

Read device status by sending `read` and getting `read_ack`

```python
plug = gateway.connected_devices['plug'][0]
print plug.read()
```

Write to device by sending `write` and getting `write_ack`
Make sure to export password as env var before using writes

```bash
$ export XIAOMI_PASSWORD=password
```

```python
plug = gateway.connected_devices['plug'][0]
print plug.write({'status': 'on'})
```

Turn on party mode for Gateway Light

```python
from time import sleep
import random
alpha = (
	"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", 
	"A", "B", "C", "D", "E", "F"
)

while True:
	color = '99%s' % ''.join([random.choice(alpha) for _ in range(6)])
	gateway.write(
		{'rgb': int(color, 16)},
		ack=False
	)
	sleep(0.2)
```

Save all devices to config

```python
from mihome.config_manager import YamlConfig

config = YamlConfig([gateway])
config.save()
```

Load config to get all devices
This saves you time from doing discovery everytime you
start up the code

```python
from mihome.config_manager import YamlConfig

config = YamlConfig()
gateways = config.load(conn, Gateway)
for gateway in gateways:
	gateway.register_subdevices()
	print gateway.connected_devices
```