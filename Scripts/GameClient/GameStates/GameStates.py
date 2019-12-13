import math

import numpy as np

from PyEngine3D.Utilities import *


class STATES:
    NONE = 0
    IDLE = 1
    PATROL = 2
    DETECTION = 3
    FIRE = 4


def get_direction(a, b):
    return normalize(a.actor_object.transform.get_pos() - b.actor_object.transform.get_pos())


def get_direction_xz(a, b):
    direction = a.actor_object.transform.get_pos() - b.actor_object.transform.get_pos()
    direction[1] = 0.0
    return normalize(direction)


def get_angle(a, b):
    direction = get_direction_xz(a, b)
    return np.dot(b.actor_object.transform.left, direction) * math.pi * 0.5


def get_distance(a, b):
    return length(a.actor_object.transform.get_pos() - b.actor_object.transform.get_pos())


def look_at_actor(a, b, rotation_speed, delta_time):
    d = get_angle(a, b)
    if rotation_speed < abs(d):
        d = np.sign(d) * rotation_speed
    b.actor_object.transform.rotation_yaw(d * delta_time)
