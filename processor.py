from glottis import Glottis
from tract import Tract


class Processor:
    def __init__(self):
        self.glottis = Glottis()
        self.tract = Tract()

    def process(self, parameterSamples, sampleIndex, bufferLength, seconds):
        outputSample = 0

        glottisSample = self.glottis.process(parameterSamples, sampleIndex, bufferLength, seconds)
        parameterSamples['glottis'] = glottisSample

        outputSample += self.tract.process(parameterSamples, sampleIndex, bufferLength, seconds)
        sampleIndex += 0.5  # process twice
        outputSample += self.tract.process(parameterSamples, sampleIndex, bufferLength, seconds)

        outputSample *= 0.125

        return outputSample


    def fast_process(self, parameterSamples, sampleIndex, bufferLength, seconds):
        outputSample = 0

        glottisSample = self.glottis.fast_process(parameterSamples, sampleIndex, bufferLength, seconds)
        parameterSamples['glottis'] = glottisSample

        outputSample = self.tract.process(parameterSamples, sampleIndex, bufferLength, seconds)

        return outputSample

    def update(self, seconds, constrictions):
        self.glottis.update()
        self.tract.update(seconds, constrictions)

