import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
        sys.stderr.reconfigure(encoding='utf-8', errors='ignore')
    except Exception:
        pass

import time
import queue
import collections
import numpy as np
import sounddevice as sd
import speech_recognition as sr

SAMPLE_RATE = 16000
BLOCK_SIZE = 1600  # 100ms chunks
SILENCE_CHUNKS_THRESHOLD = 6  # 600ms of silence ends phrase
TRIGGER_RMS_THRESHOLD = 0.006  # sensitive speech threshold

recognizer = sr.Recognizer()
audio_queue = queue.Queue()

def audio_callback(indata, frames, time_info, status):
    audio_queue.put(indata.copy())

print("==================================================", flush=True)
print("[LIVE VAD STREAM] TESTING FOR 5 SECONDS...", flush=True)
print("==================================================", flush=True)

ring_buffer = collections.deque(maxlen=10) # 1.0s pre-roll buffer
is_speaking = False
phrase_chunks = []
silent_count = 0

start_time = time.time()

with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, blocksize=BLOCK_SIZE, callback=audio_callback):
    while time.time() - start_time < 5:
        try:
            chunk = audio_queue.get(timeout=0.2)
        except queue.Empty:
            continue

        rms = float(np.sqrt(np.mean(chunk**2)))
        
        if not is_speaking:
            ring_buffer.append(chunk)
            if rms > TRIGGER_RMS_THRESHOLD:
                is_speaking = True
                print(f"\n[VAD] Voice activity started! (RMS: {rms:.4f})", flush=True)
                phrase_chunks = list(ring_buffer)
                silent_count = 0
        else:
            phrase_chunks.append(chunk)
            if rms < TRIGGER_RMS_THRESHOLD:
                silent_count += 1
                if silent_count >= SILENCE_CHUNKS_THRESHOLD:
                    print("[VAD] Phrase ended. Transcribing...", flush=True)
                    is_speaking = False
                    silent_count = 0
                    
                    full_audio = np.concatenate(phrase_chunks, axis=0)
                    audio_int16 = (full_audio * 32767).astype(np.int16)
                    audio_data = sr.AudioData(audio_int16.tobytes(), SAMPLE_RATE, 2)
                    
                    try:
                        text = recognizer.recognize_google(audio_data)
                        print(f"🎉 [TRANSCRIBED]: '{text}'", flush=True)
                    except sr.UnknownValueError:
                        print("[STT] Ambient noise (no words).", flush=True)
                    except Exception as e:
                        print(f"[STT Error]: {e}", flush=True)
                    
                    phrase_chunks = []
                    ring_buffer.clear()
            else:
                silent_count = 0

print("=== Test finished ===", flush=True)
