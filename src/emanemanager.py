#!/usr/bin/env python3

import logging
import os
import signal
import struct
import sys
import time
from argparse import ArgumentParser
from multiprocessing import shared_memory
from emane.events import EventService, EventServiceException, LocationEvent

from node import EMANENode
from sharedmem import RobotMeta, RobotPose

__version__ = '0.2.1_beta'

META_FORM = RobotMeta.FORMAT
META_SIZE = struct.calcsize(META_FORM)
META_NAME = "argos_emane_meta"
POSE_FORM = RobotPose.FORMAT
POSE_SIZE = struct.calcsize(POSE_FORM)
POSE_NAME = "argos_emane_pose"

EMANE_PID = os.getpid()
GW_ID = 65535  # GW's ARGoS ID


def handler_sigcont(sig, frame):
    return


def handler_sigterm(sig, frame):
    shm_meta.close()
    shm_pose.close()
    sys.exit(0)


def translate_id(argosID):
    global currUnassignedID
    global robotID_LUT

    # If an EMANE ID is not assigned to current ARGOS ID, assign next ID
    if argosID not in robotID_LUT:
        robotID_LUT[argosID] = currUnassignedID
        currUnassignedID += 1

    return robotID_LUT[argosID]


def wait_for_argos():
    time.sleep(0.1)
    os.kill(sys_meta.argos_pid, signal.SIGCONT)
    signal.raise_signal(signal.SIGSTOP)


def init():
    signal.signal(signal.SIGTERM, handler_sigterm)
    signal.signal(signal.SIGCONT, handler_sigcont)

    global shm_meta
    global shm_pose

    shm_meta_exists = False
    while (not shm_meta_exists):
        try:
            shm_meta = shared_memory.SharedMemory(name=META_NAME,
                                                  create=False,
                                                  size=META_SIZE)
        except FileNotFoundError:
            time.sleep(5)
            continue
        shm_meta_exists = True

    global sys_meta
    sys_meta = RobotMeta()
    sys_meta.unpack(shm_meta)
    sys_meta.emane_pid = EMANE_PID
    sys_meta.pack(shm_meta)

    logger.info("ARGoS found continuing setup")

    shm_pose = shared_memory.SharedMemory(name=POSE_NAME,
                                          create=False,
                                          size=POSE_SIZE*sys_meta.num_robot)

    global robot_nodes
    robot_nodes = [EMANENode() for i in range(sys_meta.num_robot)]

    global robot_pose
    robot_pose = [RobotPose() for i in range(sys_meta.num_robot)]

    # Set up gateway node location
#    loc_event = LocationEvent()
#    loc_event.append(254,
#                     latitude=sys_meta.gw_lat,
#                     longitude=sys_meta.gw_lon,
#                     altitude=sys_meta.gw_alt)
#    EMANEEventChannel.publish(0, loc_event)


def update_robot(prev_robot):
    global shm_meta
    global shm_pose
    global robot_nodes
    global robot_pose

    sys_meta.unpack(shm_meta)

    # This is unlikely to be called unless # of ARGoS nodes != # of EMANE nodes
    # EMANE can not create new nodes during runtime
    if (prev_robot < sys_meta.num_robot):
        shm_pose.close()
        shm_pose = shared_memory.SharedMemory(name=POSE_NAME,
                                              create=False)
        robot_pose = [RobotPose() for i in range(sys_meta.num_robot)]

    for i in range(sys_meta.num_robot):
        buf = shm_pose.buf[i*POSE_SIZE:(i+1)*POSE_SIZE] # slice current data
        robot_pose[i].unpack(buf)
        robot_nodes[i].id = robot_pose[i].id + 1 # Convert ARGoS ID to EMANE ID by adding 1
        robot_nodes[i].lat = robot_pose[i].lat
        robot_nodes[i].lon = robot_pose[i].lon
        robot_nodes[i].alt = robot_pose[i].alt

    for robot in robot_nodes:
        robot.location_event(EMANEEventChannel)


def main():
    # Program main functional loop
    # Wait for ARGoS, update data, do communication emulation, repeat
    iterNum = 1

    init()
    os.kill(sys_meta.argos_pid, signal.SIGCONT)
    while True:
        time.sleep(0.1)
        logger.debug("Begining simulation iteration {iterNum}".format(iterNum=iterNum))
        prev_robot = sys_meta.num_robot
        update_robot(prev_robot)

        iterNum += 1


if __name__ == '__main__':
    # Argument Parsing
    parser = ArgumentParser()

    parser.add_argument('-f', '--logfile',
                        metavar='FILE',
                        help='Log to a file instead of stdout.')

    parser.add_argument('--pidfile',
                        metavar='FILE',
                        help='Write application pid to file.')

    parser.add_argument('-l', '--loglevel',
                        choices=range(1, 6),
                        default=2,
                        type=int,
                        help='Set inital log level. (Default: 2)')

    parser.add_argument('-v', '--version',
                        action='version',
                        version=__version__)

    parser.add_argument('-s', '--sysfile',
                        metavar='FILE',
                        help='Experiment scenario parameters')

    args = parser.parse_args()


    # Set up Logger
    logger = logging.getLogger('managerLogger')
    logger.setLevel((args.loglevel) * 10)

    formatter = logging.Formatter('[%(levelname)s] %(message)s')

    if (args.logfile is not None):
        handler = logging.FileHandler(args.logfile, mode='a')
        handler.setLevel((args.loglevel) * 10)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    else:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel((args.loglevel) * 10)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Set up PID storage file (primarily for EMANE)
    if (args.pidfile is not None):
        with open(args.pidfile, 'w', encoding='utf-8') as f:
            f.write(str(os.getpid()))

    # Check that EMANE is running
    try:
        # HACK: Can we get this from EMANE instead of hardcode?
        EMANEEventChannel = EventService(('224.1.2.8', 45703, 'control0'))
    except EventServiceException:
        logger.error("Can not find the event channel, is EMANE running?")
        sys.exit(-1)

    main()
