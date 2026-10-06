import speech_recognition as sr
import sounddevice as sd
import numpy as np
import time

print("=== AUDIO DEVICE DIAGNOSTICS ===")
print("Available Audio Devices:")
print(sd.query_devices())

print("\nDefault Input Device:", sd.default.device[0])

print("\nTesting Live Microphone Level for 3 seconds (Say 'Hey Mahesh' loudly)...")
duration = 3  # seconds
sample_rate = 16000

recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
sd.wait()

rms = np.sqrt(np.mean(recording**2))
peak = np.max(np.abs(recording))
print(f"Recorded Audio Stats -> RMS Energy: {rms:.5f}, Peak Volume: {peak:.5f}")

if rms > 0.005:
    print("✅ Microphone is DETECTING sound clearly!")
else:
    print("⚠️ Microphone level is very low / muted in Windows settings.")
