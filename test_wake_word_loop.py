import sys
import time
import speech_recognition as sr

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

print("==================================================")
print("TESTING BACKGROUND WAKE-WORD LISTENER")
print("==================================================")

recognizer = sr.Recognizer()
recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 0.6
recognizer.non_speaking_duration = 0.4

try:
    with sr.Microphone() as source:
        print("[Microphone] Adjusting for ambient noise (1s)...")
        recognizer.adjust_for_ambient_noise(source, duration=1.0)
        print(f"[Microphone] Ambient noise set to: {recognizer.energy_threshold}")
        print("\n>>> PLEASE SAY 'Hey Mahesh' OR ANY COMMAND NOW (Testing for 10 seconds)... <<<")

        start = time.time()
        while time.time() - start < 10:
            try:
                audio = recognizer.listen(source, timeout=3.0, phrase_time_limit=5.0)
                print("[Audio] Sound detected, transcribing...")
                text = recognizer.recognize_google(audio).lower()
                print(f"[Transcribed]: '{text}'")
                if any(w in text for w in ["mahesh", "siri", "hey"]):
                    print("🎉 WAKE WORD TRIGGERED SUCCESSFULLY!")
                    break
            except sr.WaitTimeoutError:
                print(".", end="", flush=True)
            except sr.UnknownValueError:
                print("[Google STT] Sound detected but couldn't parse words.")
            except Exception as e:
                print(f"[Error] {e}")

except Exception as e:
    print(f"[Fatal Mic Error]: {e}")
