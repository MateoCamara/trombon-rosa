from processor import Processor
from parameters_descriptors import getParameterDescriptors
import sounddevice as sd
from tqdm import tqdm

if __name__ == "__main__":
    sampleRate = 48_000
    params = getParameterDescriptors()
    processor = Processor()
    currentTime = 0
    bufferLength = 128
    duration = 2
    constrictions = []

    out = []
    for i in tqdm(range(int(sampleRate * duration / 128))):
        for sampleIndex in range(bufferLength):
            seconds = currentTime + (sampleIndex/sampleRate)
            sample = processor.process(params,
                                       sampleIndex=sampleIndex,
                                       bufferLength=bufferLength,
                                       seconds=seconds)
            out.append(sample)
        currentTime = len(out) / sampleRate
        processor.update(seconds=currentTime, constrictions=constrictions)

    sd.play(out, samplerate=sampleRate, blocking=True)



