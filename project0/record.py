'''
reference:
[1]https://roytuts.com/python-voice-recording-through-microphone-for-arbitrary-time-using-pyaudio/
[2]https://dolby.io/blog/capturing-high-quality-audio-with-python-and-pyaudio/
'''

import pyaudio
import wave
import keyboard

RATE = 48000
CHANNELS = 2
CHUNK = 1024
FORMAT = pyaudio.paInt16

isEnd = False


def ceaseRecord():
    global isEnd
    isEnd = True


def record(duration=None):
    pa = pyaudio.PyAudio()
    stream = pa.open(
        rate=RATE,
        channels=CHANNELS,
        format=FORMAT,
        input=True,  # input stream flag
        input_device_index=1,  # input device index
        frames_per_buffer=CHUNK)
    sampleWidth = pa.get_sample_size(FORMAT)
    print('Recording...')
    if duration is None:
        frames = []
        keyboard.add_hotkey('space', ceaseRecord)
        print('Press space to cease')
        while not isEnd:
            data = stream.read(CHUNK)
            frames.append(data)

        inputAudio = b''.join(frames)
    else:
        inputAudio = stream.read(duration * RATE)

    print("Done")
    stream.stop_stream()
    stream.close()
    pa.terminate()

    outputFileName = 'audio-recording.wav'
    with wave.open(outputFileName, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(sampleWidth)
        wf.setframerate(RATE)
        wf.writeframes(inputAudio)


if __name__ == '__main__':
    record()
