import random

import numpy as np

from simplex import Simplex2D


def clamp(value, min, max):
    if (value <= min):
        return min
    elif (value < max):
        return value
    else:
        return max


class Glottis:
    def __init__(self):
        self.noise = Simplex2D()

        self.alpha= 0
        self.Delta=0
        self.E0= 0
        self.epsilon= 0
        self.omega= 0
        self.shift= 0
        self.Te= 0

        self.startSeconds = 0


    def process(self, parameterSamples, sampleIndex, bufferLength, seconds):

        intensity = parameterSamples['intensity']
        loudness = parameterSamples['loudness']

        vibrato = 0
        vibrato += parameterSamples['vibratoGain'] * np.sin(2 * np.pi * seconds * parameterSamples['vibratoFrequency'])
        # vibrato += 0.02 * random.uniform(-1, 1)
        # vibrato += 0.04 * random.uniform(-1, 1)
        vibrato += 0.02 * self.noise.simplex1(seconds * 0.46)
        vibrato += 0.04 * self.noise.simplex1(seconds * 0.36)


        # if (parameterSamples.vibratoWobble > 0)
        # {
        #     var
        # wobble = 0
        # wobble += 0.2 * this.noise.simplex1(seconds * 0.98)
        # wobble += 0.4 * this.noise.simplex1(seconds * 0.50)
        # vibrato += wobble * parameterSamples.vibratoWobble
        # }

        frequency = parameterSamples["frequency"]
        frequency *= (1 + vibrato)

        tenseness = parameterSamples["tenseness"]
        # tenseness += 0.10 * random.uniform(-1, 1)
        # tenseness += 0.05 * random.uniform(-1, 1)
        tenseness += 0.10 * self.noise.simplex1(seconds * 0.46)
        tenseness += 0.05 * self.noise.simplex1(seconds * 0.36)
        tenseness += (3 - tenseness) * (1 - intensity)

        period = (1 / frequency)

        secondsOffset = (seconds - self.startSeconds)

        interpolation = secondsOffset / period

        if interpolation >= 1:
            self.startSeconds = seconds + (secondsOffset % period)
            interpolation = self.startSeconds / period
            self._updateCoefficients(tenseness)

        outputSample = 0

        noiseModulator = self._getNoiseModulator(interpolation)
        noiseModulator += ((1 - (tenseness * intensity)) * 3)
        parameterSamples['noiseModulator'] = noiseModulator

        noise = parameterSamples['noise']
        noise *= noiseModulator
        noise *= intensity
        noise *= intensity
        noise *= (1 - np.sqrt(np.max(tenseness, 0)))
        noise *= (0.02 * self.noise.simplex1(seconds * 1.99)) + 0.2

        voice = self._getNormalizedWaveform(interpolation)
        voice *= intensity
        voice *= loudness

        outputSample = noise + voice
        outputSample *= intensity

        return outputSample

    def fast_process(self, parameterSamples, sampleIndex, bufferLength, seconds):
        intensity = parameterSamples['intensity']
        loudness = parameterSamples['loudness']

        frequency = parameterSamples["frequency"]

        tenseness = parameterSamples["tenseness"]
        tenseness += 0.10 * random.uniform(-1, 1)
        tenseness += 0.05 * random.uniform(-1, 1)
        tenseness += (3 - tenseness) * (1 - intensity)

        period = (1 / frequency)

        secondsOffset = (seconds - self.startSeconds)

        interpolation = secondsOffset / period

        noise = parameterSamples['noise']
        noise *= intensity
        noise *= intensity
        noise *= (1 - np.sqrt(np.max(tenseness, 0)))
        noise *= (0.02 * random.uniform(-1, 1)) + 0.2

        voice = self._getNormalizedWaveform(interpolation)
        voice *= intensity
        voice *= loudness

        outputSample = noise + voice
        outputSample *= intensity

        return outputSample


    def update(self):
        pass

    def _updateCoefficients(self, tenseness=0):

        R = {}
        R["d"] = clamp(3 * (1 - tenseness), 0.5, 2.7)
        R["a"] = -0.01 + 0.048 * R['d']
        R["k"] = 0.224 + 0.118 * R['d']
        R["g"] = (R['k'] / 4) * (0.5 + 1.2 * R['k']) / (0.11 * R['d'] - R["a"] * (0.5 + 1.2 * R['k']))

        T = {}
        T["a"] = R["a"]
        T["p"] = 1 / (2 * R["g"])
        T["e"] = T["p"] + T["p"] * R["k"]

        self.epsilon = 1 / T["a"]
        self.shift = np.exp(-self.epsilon * (1 - T["e"]))
        self.Delta = 1 - self.shift

        integral = {}
        integral["RHS"] = ((1 / self.epsilon) * (self.shift - 1) + (
                    1 - T["e"]) * self.shift) / self.Delta
        integral["total"] = {}
        integral["total"]["lower"] = -(T['e'] - T['p']) / 2 + integral["RHS"]
        integral["total"]["upper"] = -integral["total"]["lower"]

        self.omega = np.pi / T["p"]

        s = np.sin(self.omega * T["e"])
        y = -np.pi * s * integral["total"]["upper"] / (T["p"] * 2)
        z = np.log(y)

        self.alpha = z / (T["p"] / 2 - T["e"])
        self.E0 = -1 / (s * np.exp(self.alpha * T["e"]))
        self.Te = T["e"]


    def _getNormalizedWaveform(self, interpolation):

        return (-np.exp(-self.epsilon * (\
                    interpolation - self.Te)) + self.shift) / self.Delta\
        if (interpolation > self.Te) else \
        self.E0 * np.exp(self.alpha * interpolation) * np.sin(\
            self.omega * interpolation)


    def _getNoiseModulator(self, interpolation):
        angle = 2 * np.pi * interpolation
        amplitude = np.sin(angle)
        positiveAmplitude = max(0, amplitude)
        offset = 0.1
        gain = 0.2
        noiseModulator = ((positiveAmplitude * gain) + offset)
        
        return noiseModulator
