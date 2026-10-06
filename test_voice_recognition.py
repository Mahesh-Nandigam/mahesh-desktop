import sounddevice as sd
import numpy as np
import speech_recognition as sr
import traceback
import sys

# Ensure UTF-8 output encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

print("==================================================")
print("🎙️ LIVE VOICE RECOGNITION TEST")
print("Speak clearly into your mic for 4 seconds now (e.g. 'Hey Mahesh open VS Code'):")
print("==================================================")

sample_rate = 16000
duration = 4 # seconds

try:
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
    sd.wait()

    rms = np.sqrt(np.mean(recording**2))
    peak = np.max(np.abs(recording))
    print(f"\n[Audio Stats] RMS Energy: {rms:.5f} | Peak: {peak:.5f}")

    if rms < 0.001:
        print("[WARNING] Audio is near-zero silence! Check if Windows Mic is muted or disabled.")
    else:
        print("[INFO] Audio captured successfully. Sending to Speech-to-Text...")

        # Convert float32 to int16 PCM
        audio_int16 = (recording * 32767).astype(np.int16)
        audio_bytes = audio_int16.tobytes()

        recognizer = sr.Recognizer()
        audio_data = sr.AudioData(audio_bytes, sample_rate, 2)

        try:
            transcript = recognizer.recognize_google(audio_data)
            print(f"\n✅ [RECOGNIZED TRANSCRIPT]: \"{transcript}\"")
        except sr.UnknownValueError:
            print("\n❌ [Google STT]: Audio was recorded, but Google STT could not understand the words (UnknownValueError).")
        except sr.RequestError as e:
            print(f"\n❌ [Google STT Network Error]: Could not reach Google STT server: {e}")
except Exception as e:
    print(f"\n❌ [Fatal Error]: {e}")
    traceback.print_exc()
