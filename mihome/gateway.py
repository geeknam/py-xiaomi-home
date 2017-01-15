import json
from collections import defaultdict

from mihome.base import BaseXiaomiDevice
from mihome import devices


class Gateway(BaseXiaomiDevice):

    model = 'gateway'

    def __init__(self, connection, sid, ip, port, subdevices=None):
        self.connection = connection
        self.sid = sid
        self.ip = ip
        self.port = port
        self.subdevices = subdevices or []
        # categorised by model
        self.connected_devices = defaultdict(list)

    def serialise(self):
        return {
            'sid': self.sid,
            'ip': self.ip,
            'port': self.port,
            'model': self.model,
            'subdevices': self.subdevices
        }

    @classmethod
    def deserialise(cls, connection, data):
        gateways = []
        for gateway_data in data:
            gateway_data.pop('model')
            gateway_instance = cls(connection, **gateway_data)

            gateways.append(
                cls(connection, **gateway_data)
            )
        return gateways

    def get_id_list(self):
        self.connection.send({'cmd': 'get_id_list'}, ip=self.ip)
        return self.connection.receive(cmd='get_id_list_ack')

    def get_token(self):
        return self.connection.receive(cmd='heartbeat')['token']

    def get_subdevices(self, force=False):
        if self.subdevices and not force:
            return self.subdevices
        self.subdevices = []
        sids = json.loads(self.get_id_list()['data'])
        for sid in sids:
            self.connection.send(
                {'cmd': 'read', 'sid': sid},
                ip=self.ip
            )
            device_status = self.connection.receive(cmd='read_ack')
            device_status.pop('cmd')
            device_status.pop('data')
            self.subdevices.append(device_status)
        return self.subdevices

    def register_subdevices(self):
        device_class_map = {
            '': devices.Switch,
            'switch': devices.Switch,
            'motion': devices.MotionSensor,
            'magnet': devices.DoorMagnet,
            'plug': devices.Plug
        }
        for device in self.get_subdevices():
            device_class = device_class_map[device['model']]
            self.connected_devices[device['model']].append(
                device_class(self.connection, self, device['sid'], device['short_id'])
            )

