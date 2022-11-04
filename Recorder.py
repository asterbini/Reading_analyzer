import queue
import sys
import os
import glob
import time
from datetime  import datetime

import sounddevice as sd
import soundfile as sf
from pydub import AudioSegment
import numpy
assert numpy

q = queue.Queue()
rec = False

def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(indata.copy())
    
def convert():
    global rec
    rec = False
    time.sleep(0.5)
    files = glob.glob('audio/*.wav')
    if len(files) > 0:
        file = max(files, key=os.path.getctime)
    else:
        return 0
    f = file
    file = file[:-4]
    flacFile = AudioSegment.from_wav(f'{file}.wav')
    flacFile.export(f'{file}.flac', format='flac')
    #os.remove(f)
    return 0
    
def record():
    now = datetime.now()
    dt_string = now.strftime('%Y_%m_%d_%H_%M_%S')
    with sf.SoundFile(f'audio/{dt_string}.wav', mode='x', samplerate=44100, channels=2, subtype=None) as file:
        with sd.InputStream(samplerate=44100, channels=2, callback=callback):
            print('#' * 80)
            print('Starting recording...')
            print('#' * 80)
            global rec
            rec = True
            while rec:
                if not rec:
                    break
                file.write(q.get())
            return 0
        
if __name__ == '__main__':
    globals()[sys.argv[1]]()
        

    