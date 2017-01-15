from mihome.base import BaseXiaomiDevice


class Switch(BaseXiaomiDevice):

    model = 'switch'


class DoorMagnet(BaseXiaomiDevice):

    model = 'magnet'


class MotionSensor(BaseXiaomiDevice):

    model = 'motion'


class Plug(BaseXiaomiDevice):

    model = 'plug'


class Cube(BaseXiaomiDevice):

    model = 'cube'
