import json
from collections import defaultdict
from datetime import datetime, timedelta

from mihome.base import BaseXiaomiDevice
from mihome import devices


DEVICE_CLASS_MAP = {
    'cube': devices.Cube,
    'switch': devices.Switch,
    'motion': devices.MotionSensor,
    'magnet': devices.DoorMagnet,
    'plug': devices.Plug
}


class Gateway(BaseXiaomiDevice):

    model = 'gateway'

    def __init__(self, connection, sid, ip, port, subdevices=None):
        self.connection = connection
        self.sid = sid
        self.short_id = 0
        self.ip = ip
        self.port = port
        self.subdevices = subdevices or []
        # categorised by model
        self.connected_devices = defaultdict(list)
        self._token = None
        self.last_token_update = None

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

    @property
    def should_update_token(self):
        if not self._token:
            return True
        delta = datetime.now() - self.last_token_update
        return delta > timedelta(seconds=10)

    def get_token(self):
        if not self.should_update_token:
            return self._token
        self._token = self.connection.receive(cmd='heartbeat')['token']
        self.last_token_update = datetime.now()
        return self._token

    def get_gateway_ip(self):
        return self.ip

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

        for device in self.get_subdevices():
            device_class = DEVICE_CLASS_MAP[device['model']]
            self.connected_devices[device['model']].append(
                device_class(self.connection, self, device['sid'], device['short_id'])
            )

