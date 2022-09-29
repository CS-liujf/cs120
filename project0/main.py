from record import record
from play import play
import threading
from pyaudio import PyAudio

p=PyAudio()
# CK1
record(p,10)
print("start playing")
play("./audio-recording.wav",p,10)

# CK2
input("Start next test?")
# record and play default music
t1 = threading.Thread(target=record, kwargs={"duration": 11, "pa":p})
t2 = threading.Thread(target=play, args=("default_music.wav", p, 10))

t1.start()
t2.start()
t1.join()
t2.join()

play("./audio-recording.wav",p, 10)
p.terminate()
