import sys
import os
import time
import numpy as np
import sounddevice as sd
import speech_recognition as sr

log_file = "test_siri_diag.log"

def log(msg):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

with open(log_file, "w", encoding="utf-8") as f:
    f.write("=== SIRI DIAGNOSTIC START ===\n")

log("Checking audio input devices...")
devices = sd.query_devices()
log(f"Default input: {sd.default.device[0]}")

log("Recording 3 seconds from default input device...")
sample_rate = 16000
rec = sd.rec(int(3 * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
sd.wait()

rms = float(np.sqrt(np.mean(rec**2)))
peak = float(np.max(np.abs(rec)))
log(f"Audio stats: RMS={rms:.5f}, Peak={peak:.5f}")

log("Testing SpeechRecognition AudioData conversion...")
rec_int16 = (rec * 32767).astype(np.int16)
audio_data = sr.AudioData(rec_int16.tobytes(), sample_rate, 2)

recognizer = sr.Recognizer()
try:
    log("Sending to Google STT...")
    text = recognizer.recognize_google(audio_data)
    log(f"SUCCESS! Transcribed: '{text}'")
except sr.UnknownValueError:
    log("Google STT: No distinct words recognized (silence or ambient noise).")
except Exception as e:
    log(f"STT Exception: {e}")

log("=== DIAGNOSTIC COMPLETE ===")
