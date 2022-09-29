import numpy as np


class Transient:
    def __init__(self, position, seconds):
        self.position = position

        self.startTime = seconds
        self.timeAlive = 0
        self.lifetime = 0.2

        self.strength = 0.3
        self.exponent = 200

    def get_amplitude(self):
        return self.strength * np.pow(-2, self.timeAlive * self.exponent)

    def get_isAlive(self):
        return self.timeAlive < self.lifetime

    def update(self, seconds):
        self.timeAlive = seconds - self.startTime
