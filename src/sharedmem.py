import struct
from ctypes import c_double, c_int32, c_uint16, c_uint32
from dataclasses import dataclass
from typing import ClassVar

@dataclass
class RobotMeta():
    """
    Struct containing metadata shared between ARGoS and EMANE

    Attributes
    ----------
    num_robot - Number of active robots
    num_comms - Number of robots attmempting to broadcast
    deltaT    - Time per step
    argos_pid - ARGoS Process ID
    emane_pid - EMANE Process ID (PID of Interface Script, not EMANE itself)
    gw_lat    - Gateway Node latitude
    gw_lon    - Gateway Node longitude
    alt    - Gateway Node altitude
    FORMAT - Metadata used to unpack data from shared memory
    """
    num_robot:  c_uint16 = None
    deltaT:     c_double = None
    argos_pid:  c_int32 = None
    emane_pid:  c_int32 = None
    gw_lat:     c_double = None
    gw_lon:     c_double = None
    gw_alt:     c_double = None
    FORMAT: ClassVar[str] = 'Hdiiddd'

    def unpack(self, shm):
        self.num_robot,self.deltaT, self.argos_pid, self.emane_pid, self.gw_lat, self.gw_lon, self.gw_alt = struct.unpack(self.FORMAT, shm.buf.tobytes())

    def pack(self, shm):
        buf = struct.pack(self.FORMAT, self.num_robot, self.deltaT, self.argos_pid, self.emane_pid, self.gw_lat, self.gw_lon, self.gw_alt)
        shm.buf[:struct.calcsize(self.FORMAT)] = buf


@dataclass
class RobotPose():
    """
    Struct containing location of each robot

    Attributes
    ----------
    id - Robot ARGoS ID (not EMANE ID)
    lat - Latitude of robot
    lon - Longitude of robot
    alt - Altitude of robot
    FORMAT - Metadata used to unpack data from shared memory
    """
    id: c_uint32 = None
    lat: c_double = None
    lon: c_double = None
    alt: c_double = None
    FORMAT: ClassVar[str] = 'Iddd'

    def unpack(self, buf):
        self.id, self.lat, self.lon, self.alt = struct.unpack(self.FORMAT, buf)

    def pack(self):
        buf = struct.pack(self.FORMAT, self.id, self.lat, self.lon, self.alt)
        return buf
