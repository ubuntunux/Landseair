import numpy as np

from PyEngine3D.Utilities import *


class CameraShake:
    MIN_CAMERA_SHAKE_TERM = 0.0
    MAX_CAMERA_SHAKE_TERM = 0.05

    def __init__(self):
        self.elapsed_time = 0.0
        self.prev_camera_shake_time = 0.0
        self.next_camera_shake_time = 0.0
        self.total_camera_shake_time = 0.0
        self.camera_shake_intensity = 0.0
        self.camera_shake_amount = Float2(0.0, 0.0)
        self.prev_camera_shake_amount = Float2(0.0, 0.0)
        self.next_camera_shake_amount = Float2(0.0, 0.0)

    def get_camera_shake(self):
        return self.camera_shake_amount

    def set_camera_shake(self, total_camera_shake_time, camera_shake_intensity):
        self.elapsed_time = 0.0
        self.prev_camera_shake_time = 0.0
        self.next_camera_shake_time = self.MIN_CAMERA_SHAKE_TERM + (np.random.random() * (self.MAX_CAMERA_SHAKE_TERM - self.MIN_CAMERA_SHAKE_TERM))
        self.total_camera_shake_time = total_camera_shake_time
        self.camera_shake_intensity = camera_shake_intensity
        self.camera_shake_amount[0] = 0.0
        self.camera_shake_amount[1] = 0.0
        self.prev_camera_shake_amount[0] = 0.0
        self.prev_camera_shake_amount[1] = 0.0
        self.next_camera_shake_amount[0] = (np.random.random() * 2.0 - 1.0) * self.camera_shake_intensity
        self.next_camera_shake_amount[1] = (np.random.random() * 2.0 - 1.0) * self.camera_shake_intensity

    def update(self, delta_time):
        if self.elapsed_time < self.total_camera_shake_time:
            if self.elapsed_time < self.next_camera_shake_time:
                ratio = 1.0 - pow(min(1.0, self.elapsed_time / self.total_camera_shake_time), 0.5)
                t = max(0.0, min(1.0, (self.next_camera_shake_time - self.elapsed_time) / (self.next_camera_shake_time - self.prev_camera_shake_time)))
                self.camera_shake_amount[...] = lerp(self.prev_camera_shake_amount, self.next_camera_shake_amount, t) * ratio

            self.elapsed_time += delta_time
            if self.total_camera_shake_time <= self.elapsed_time:
                self.camera_shake_amount[0] = 0.0
                self.camera_shake_amount[1] = 0.0
            elif self.next_camera_shake_time <= self.elapsed_time:
                self.prev_camera_shake_time = self.next_camera_shake_time
                self.prev_camera_shake_amount[...] = self.next_camera_shake_amount
                self.next_camera_shake_time += self.MIN_CAMERA_SHAKE_TERM + (np.random.random() * (self.MAX_CAMERA_SHAKE_TERM - self.MIN_CAMERA_SHAKE_TERM))
                if self.total_camera_shake_time <= self.next_camera_shake_time:
                    self.next_camera_shake_time = self.total_camera_shake_time
                    self.next_camera_shake_amount[0] = 0.0
                    self.next_camera_shake_amount[1] = 0.0
                else:
                    self.next_camera_shake_amount[0] = (np.random.random() * 2.0 - 1.0) * self.camera_shake_intensity
                    self.next_camera_shake_amount[1] = (np.random.random() * 2.0 - 1.0) * self.camera_shake_intensity
