import numpy as np


class Nose:
    def __init__(self, tract):
        self.length = int(np.floor(28 * tract.length / 44))

        self.start = tract.length - self.length + 1;
        
        self.fade = 1;
        self.offset = 0.8;
        
        # buffers
        self.left = list(np.zeros(self.length))
        self.left_junction = list(np.zeros(self.length+1))
        self.right = list(np.zeros(self.length))
        self.right_junction = list(np.zeros(self.length+1))
        self.reflection = []
        self.diameter = []
        self.amplitude = []
        self.amplitude_max = list(np.zeros(self.length))
        self.reflection_value = 0
        self.reflection_new = 0
        
        # setup
        for index in range(self.length):
            interpolation = index / self.length

            value = 0.4 + 1.6 * (2 * interpolation) if (interpolation < 0.5) else 0.5 + 1.5 * (2 - (2 * interpolation))

            self.diameter.append(min(value, 1.9))

        for index in range(self.length):
            self.amplitude.append(self.diameter[index]**2)

            if index > 0:
                self.reflection.append((self.amplitude[index-1] - self.amplitude[index]) / (self.amplitude[index-1] + self.amplitude[index]))
            else:
                self.reflection.append(0)

        self.diameter[0] = tract.velum['target']
