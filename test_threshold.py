import sounddevice as sd
import numpy as np
import time

print("Listening for 5 seconds... Speak 'Hey Mahesh' in normal voice now:")

def callback(indata, frames, time, status):
    volume_norm = np.linalg.norm(indata) * 10
    peak = np.max(np.abs(indata))
    if volume_norm > 0.1:
        print(f"--> [SOUND DETECTED] Volume Norm: {volume_norm:.4f}, Peak: {peak:.4f}")

with sd.InputStream(callback=callback, channels=1, samplerate=16000, blocksize=4000):
    time.sleep(5)
