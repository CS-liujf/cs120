import wave
import sys


def play(filename=None, pa=None, duration=None):
    if not pa:
        return

    # size per data
    CHUNK = 512

    if not filename:
        filename = sys.argv[1]
    # open a wav
    wf = wave.open(filename, 'rb')
    fs = wf.getframerate()

    # open a new stream
    stream = pa.open(format=pa.get_format_from_width(wf.getsampwidth()),
                     channels=wf.getnchannels(),
                     rate=fs,
                     output=True)

    for _ in range(duration*fs//CHUNK+1):
        data = wf.readframes(CHUNK)
        # play that piece of audio data
        stream.write(data)

    stream.stop_stream()
    stream.close()
