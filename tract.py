import random

import numpy as np

from nose import Nose
from transient import Transient


def interpolate(interpolation, fra, to):
    return (fra * (1 - interpolation) + (to * interpolation))


def clamp(value, minValue, maxValue):
    return minValue if (value <= minValue) else maxValue


def get_range(max_val, min_val):
    return max_val - min_val


def get_center(max_val, min_val):
    return (max_val + min_val) / 2


class Tract:
    def __init__(self, length=44):
        self.length = length

        # Indices
        self.blade = {
            "start": np.floor(10 * self.length / 44),
        }

        self.tip = {
            "start": np.floor(32 * self.length / 44),
        };

        self.lip = {
            "start": np.floor(39 * self.length / 44),
            "reflection": -0.85,
        };

        self.glottis = {
            "reflection": 0.75
        };

        self.velum = {
            "target": 0.01,
        };

        self.grid = {
            "offset": 1.7,
        };

        # Buffers
        self.right = list(np.zeros(self.length))
        self.right_junction = list(np.zeros(self.length+1))
        self.right_reflection = {
            "value": 0,
            "new": 0,
        }
        self.right_reflection_new = 0

        self.left = list(np.zeros(self.length))
        self.left_junction = list(np.zeros(self.length+1))
        self.left_reflection = {
            "value": 0,
            "new": 0,
        }
        self.left_reflection_new = 0

        self.reflection = list(np.zeros(self.length))
        self.reflection_new = list(np.zeros(self.length))

        self.amplitude = list(np.zeros(self.length))
        self.amplitude_max = list(np.zeros(self.length))

        self.diameter = list(np.zeros(self.length))
        self.diameter_rest = list(np.zeros(self.length))

        # Tongue & Nose
        self.tongue = {
            "_diameter": 2.43,
            "_index": 12.9,

            "range": {
                "diameter": {
                    "minValue": 2.05,
                    "maxValue": 3.5
                },

                "index": {
                    "minValue": self.blade['start'] + 2,
                    "maxValue": self.tip['start'] - 3,
                }
            }
        }


        # NOSE
        self.nose = Nose(self)

        # Transients
        self.transients = []
        self.transients_obstruction = {
            "last": -1,
            "new": -1,
        }

        # Constrictions
        self.previousConstrictions = []
        self.previousConstrictions_tongue = {}

        # diameter.update
        for index in range(self.length):
            if index < (7 * self.length / 44 - 0.5):
                value = 0.6
            elif index < (12 * self.length / 44):
                value = 1.1
            else:
                value = 1.5

            self.diameter[index] = value
            self.diameter_rest[index] = value


        self._updateReflection()


    # PROCESS
    def process(self, parameterSamples, sampleIndex, bufferLength, seconds):
        self.tongue["diameter"] = parameterSamples["tongueDiameter"]
        self.tongue["index"] = parameterSamples["tongueIndex"]

        self._processTransients(seconds)
        self._processConstrictions(self.previousConstrictions, parameterSamples)

        bufferInterpolation = sampleIndex / bufferLength
        updateAmplitudes = random.random() < 0.1

        outputSample = 0
        outputSample += self._processLips(parameterSamples, bufferInterpolation, updateAmplitudes)

        outputSample += self._processNose(parameterSamples, bufferInterpolation, updateAmplitudes)

        if np.isnan(outputSample):
            self.reset()

        return outputSample

    def _processTransients(self, seconds):
        for index in reversed(range(len(self.transients))):
            transient = self.transients[index]
            self.left[transient['position']] += transient["amplitude"]
            transient.update(seconds)

            if not transient["isAlive"]:
                self.transients["splice"](index, 1)

    def _processConstrictions(self, constrictions, parameterSamples):

        for index, constriction in enumerate(constrictions):

            if (constriction.index >= 2) and (constriction.index <= self.length) and (constriction.diameter > 0):
                noise = parameterSamples["glottis"]
                noiseScalar = parameterSamples["noiseModulator"] * 0.66;
                noise *= noiseScalar

                thinness = clamp(8 * (0.7 - constriction.diameter), 0, 1);
                openness = clamp(30 * (constriction.diameter - 0.3), 0, 1);
                _ness = thinness * openness;
                noise *= _ness / 2;

                lowerIndex = np.floor(constriction.index);
                lowerWeight = constriction.index - lowerIndex;
                lowerNoise = noise * lowerWeight;

                upperIndex = lowerIndex + 1;
                upperWeight = upperIndex - constriction.index;
                upperNoise = noise * upperWeight;

                self.right[lowerIndex + 1] += lowerNoise;
                self.right[upperIndex + 1] += upperNoise;

                self.left[lowerIndex + 1] += lowerNoise;
                self.left[upperIndex + 1] += upperNoise;

    def _processLips(self, parameterSamples, bufferInterpolation, updateAmplitudes):
        if not self.left:
            self.left.append(0)

        self.right_junction[0] = self.left[0] * self.glottis["reflection"] + parameterSamples["glottis"]
        self.left_junction[self.length] = self.right[self.length - 1] * self.lip["reflection"]

        # for index in range(self.length):
        #     if index == 0:
        #         continue
        #     interpolation = interpolate(bufferInterpolation, self.reflection[index], self.reflection_new[index])
        #     print(interpolation)
        #     offset = interpolation * (self.right[index-1] + self.left[index])
        #
        #     self.right_junction[index] = self.right[index-1] - offset
        #     self.left_junction[index] = self.left[index] + offset


        leftInterpolation = interpolate(bufferInterpolation, self.left_reflection_new, self.left_reflection['value'])
        self.left_junction[self.nose.start] = leftInterpolation * self.right[self.nose.start - 1] + (leftInterpolation + 1) * (
                self.nose.left[0] + self.left[self.nose.start])

        rightInterpolation = interpolate(bufferInterpolation, self.right_reflection_new, self.right_reflection['value'])
        self.right_junction[self.nose.start] = rightInterpolation * self.left[self.nose.start] + (rightInterpolation + 1) * (
                self.nose.left[0] + self.right[self.nose.start - 1])

        noseInterpolation = interpolate(bufferInterpolation, self.nose.reflection_new, self.nose.reflection_value)
        self.nose.right_junction[0] = noseInterpolation * self.nose.left[0] + (noseInterpolation + 1) * (
                self.left[self.nose.start] + self.right[self.nose.start - 1])

        self.right = [i * 0.999 for i in self.right_junction[:-1]]
        self.left = [i * 0.999 for i in self.left_junction[:-1]]

        if updateAmplitudes:
            suma = np.abs(self.left + self.right)
            self.amplitude_max = [i if i > j else j*0.999 for i, j in zip(suma, self.amplitude_max)]

        # for index in range(self.length):
        #     self.right[index] = self.right_junction[index] * 0.999
        #     self.left[index] = self.left_junction[index + 1] * 0.999
        #
        #     if updateAmplitudes:
        #         suma = np.abs(self.left[index] + self.right[index])
        #         self.amplitude_max[index] = suma if (suma > self.amplitude_max[index]) else self.amplitude_max[index] * 0.999


        return self.right[self.length - 1]

    def _processNose(self, parameterSamples, bufferInterpolation, updateAmplitudes):

        self.nose.left_junction[self.nose.length] = self.nose.right[self.nose.length - 1] * self.lip['reflection']

        aux_nose_right = [0] + self.nose.right[:-1]

        offset = np.array(self.nose.reflection) * (np.array(self.nose.left) + np.array(aux_nose_right))
        self.nose.left_junction = [0] + list(self.nose.left + offset)
        self.nose.right_junction = [0] + list(aux_nose_right - offset)

        # for index in range(self.nose.length):
        #     if index == 0:
        #         continue
        #
        #     offset = self.nose.reflection[index] * (self.nose.left[index] + self.nose.right[index-1])
        #
        #     self.nose.left_junction[index] = self.nose.left[index] + offset
        #     self.nose.right_junction[index] = self.nose.right[index-1] - offset

        aux_nose_left = self.nose.left[1:] + [0]

        self.nose.left = list(np.array(aux_nose_left) * np.array(self.nose.fade))
        self.nose.right = [i * self.nose.fade for i in self.nose.right_junction[:-1]]

        if (updateAmplitudes):
            suma = np.abs(np.array(self.nose.left) + np.array(self.nose.right))
            self.nose.amplitude_max = [i if i > j else j * 0.999 for i, j in zip(suma, self.nose.amplitude_max)]

        # for index in range(self.nose.length):
        #
        #     self.nose.left[index] = self.nose.left_junction[index+1] * self.nose.fade
        #     self.nose.right[index] = self.nose.right_junction[index] * self.nose.fade
        #
        #     if (updateAmplitudes):
        #         suma = np.abs(self.nose.left[index] + self.nose.right[index])
        #         self.nose.amplitude_max[index] = suma if suma > self.nose.amplitude_max[index] else self.nose.amplitude_max[index] * 0.999


        return self.nose.right[self.nose.length - 1];


    def _updateReflection(self):
        for index in range(self.length):
            self.amplitude.append(self.diameter[index] ** 2)

            if self.reflection:
                self.reflection[index] = self.reflection_new[index]
                self.reflection_new[index] = 0.999 if (self.amplitude[index] == 0) else (self.amplitude[index - 1] - self.amplitude[index]) / (
                            self.amplitude[index - 1] + self.amplitude[index])

        suma = self.amplitude[self.nose.start] + self.amplitude[self.nose.start+1] + self.nose.amplitude[0]
        self.left_reflection['value'] = self.left_reflection_new
        self.left_reflection_new = (2 * self.amplitude[self.nose.start] - suma) / suma

        self.right_reflection['value'] = self.right_reflection_new
        self.right_reflection_new = (2 * self.amplitude[self.nose.start + 1] - suma) / suma

        self.nose.reflection_value = self.nose.reflection_new
        self.nose.reflection_new = (2 * self.nose.amplitude[0] - suma) / suma

    def update(self, seconds, constrictions):
        self._updateTract()

        self._updateTransients(seconds)

        self.nose.diameter[0] = self.velum['target']
        self.nose.amplitude[0] = self.nose.diameter[0]**2

        self._updateReflection()

        self._updateConstrictions(constrictions)

    def _updateTract(self):
        for index, value in enumerate(self.diameter):
            if value <= 0:
                self.transients_obstruction['new'] = index

    def _updateTransients(self, seconds):
        if self.nose.amplitude[0] < 0.05:
            if (self.transients_obstruction['last'] > -1) and (self.transients_obstruction['new'] == -1):
                self.transients.append(Transient(self.transients_obstruction['new'], seconds=seconds))
            self.transients_obstruction['last'] = self.transients_obstruction['new']

    def _updateReflection(self):
        for index in range(self.length):
            self.amplitude[index] = self.diameter[index]**2

            if index > 0:
                self.reflection[index] = self.reflection_new[index]
                self.reflection_new[index] = 0.999 if (self.amplitude[index] == 0) else (self.amplitude[index-1] - self.amplitude[index]) / (self.amplitude[index-1] + self.amplitude[index]);
                
        suma = self.amplitude[self.nose.start] + self.amplitude[self.nose.start+1] + self.nose.amplitude[0]
        self.left_reflection['value'] = self.left_reflection['new']
        self.left_reflection['new'] = (2 * self.amplitude[self.nose.start] - suma) / suma

        self.right_reflection['value'] = self.right_reflection['new']
        self.right_reflection['new'] = (2 * self.amplitude[self.nose.start + 1] - suma) / suma

        self.nose.reflection_value = self.nose.reflection_new
        self.nose.reflection_new = (2 * self.nose.amplitude[0] - suma) / suma

    def _updateConstrictions(self, constrictions):
        update = False

        update = update or (self.tongue['index'] != self.previousConstrictions_tongue.get('index', False)) or (self.tongue['diameter'] != self.previousConstrictions_tongue.get("diameter", False))

        maxIndex = max(len(self.previousConstrictions), len(constrictions))

        for index in range(len(constrictions)):
            A = constrictions[index]
            B = self.previousConstrictions[index]
            if not A and not B:
                update = (A['index'] != B['index']) or (A['diameter'] != B['diameter'])
            else:
                update = not(A and B)

        if update:
            self._updateDiameterRest()
            self.diameter = self.diameter_rest

            self.velum['target'] = 0.01

            for index in range(len(constrictions) + 1):
                if index == 0:
                    constriction = self.tongue
                else:
                    constriction = constrictions[index]

                if (constriction['index'] > self.nose.start) and (constriction['diameter'] < -self.nose.offset):
                    self.velum['target'] = 0.4

                if (constriction['index'] >= 2) and (constriction['index'] < self.length) and (constriction['diameter'] > -(0.85 + self.nose.offset)):
                    newTractDiameter = constriction['diameter']
                    newTractDiameter -= 0.3
                    newTractDiameter = max(0.0, newTractDiameter)

                    if newTractDiameter < 3:
                        tractIndexRange = 2

                        if constriction['index'] < 25:
                            tractIndexRange = 10
                        elif constriction['index'] >= self.tip['start']:
                            tractIndexRange = 5
                        else:
                            tractIndexRange = 10 - 5 * (constriction['index'] - 25) / (self.tip['start'] - 25)

                        constrictionIndex = np.round(constriction['index'])
                        constrictionIndexRadius = np.ceil(tractIndexRange) + 1

                        tractIndex = int(constrictionIndex - constrictionIndexRadius)

                        while True:
                            if not((tractIndex < constrictionIndex + tractIndexRange+1) and ((tractIndex >= 0) and (tractIndex < self.length))):
                                break
                            tractIndexOffset = abs(tractIndex - constriction['index']) - 0.5

                            if tractIndexOffset <= 0:
                                tractDiameterScalar = 0
                            elif tractIndexOffset > tractIndexRange:
                                tractDiameterScalar = 1
                            else:
                                tractDiameterScalar = 0.5 * (1 - np.cos(np.pi * tractIndexOffset / tractIndexRange))

                            tractDiameterDifference = self.diameter[tractIndex] - newTractDiameter

                            if tractDiameterDifference > 0:
                                self.diameter[tractIndex] = newTractDiameter + tractDiameterDifference * tractDiameterScalar

                            tractIndex += 1

            self.previousConstrictions = constrictions
            self.previousConstrictions_tongue = {
                'index': self.tongue['index'],
                'diameter': self.tongue['diameter'],
            }

    def _updateDiameterRest(self):
        index = self.blade['start']
        
        while True:
            if not(index < self.lip['start']):
                break

            interpolation = (self.tongue['index'] - index) / (self.tip['start'] - self.blade['start'])

            angle = 1.1 * np.pi * interpolation
            diameter = 2 + (self.tongue['diameter'] - 2) / 1.5

            curve = (1.5 - diameter + self.grid['offset']) * np.cos(angle)

            if (index == (self.blade['start'] - 2)) or (index == (self.lip['start'] - 1)):
                curve *= 0.80

            if (index == (self.blade['start'] + 0)) or (index == (self.lip['start'] - 2)):
                curve *= 0.94

            value = 1.5 - curve

            self.diameter_rest[int(index)] = value
            index += 1

    def reset(self):
        self.right = list(np.zeros(self.length))
        self.right_junction = list(np.zeros(self.length+1))
        self.left = list(np.zeros(self.length))
        self.left_junction = list(np.zeros(self.length+1))
        self.nose.left = list(np.zeros(self.length))
        self.nose.left_junction = list(np.zeros(self.length+1))
        self.nose.right = list(np.zeros(self.length))
        self.nose.right_junction = list(np.zeros(self.length+1))
