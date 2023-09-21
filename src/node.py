from ctypes import c_ushort, c_double
from dataclasses import dataclass

from emane.events import LocationEvent


@dataclass
class EMANENode():
    """
    Corresponds to a single robot node
    Holds its own EMANE ID, Location, and TxBufferSize

    Attributes
    ----------
    id - Robot EMANE ID
    lat - Node's latitude
    lon - Node's longitude
    alt - Node's altitude
    buff - Number of bytes this node needs to still transmit
    sent - Number of bytes this node sent this iteration
    """
    id:   c_ushort = None
    lat:  c_double = None
    lon:  c_double = None
    alt:  c_double = None
    buff: c_double = 0.0

    def inc_buffer(self, size):
        self.buff += size

    def dec_buffer(self, size):
        self.buff -= size

    def location_event(self, service):
        loc_event = LocationEvent()
        loc_event.append(self.id,
                         latitude=self.lat,
                         longitude=self.lon,
                         altitude=self.alt,
                         yaw=0,
                         pitch=0,
                         roll=0)
        service.publish(0, loc_event)
