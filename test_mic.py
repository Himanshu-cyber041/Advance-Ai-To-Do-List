"""
test_mic.py
-----------
Run this DIRECTLY (not through the GUI) to check if your microphone
setup works at all:

    python test_mic.py

It will:
  1. List all microphones your system can see (with their index numbers)
  2. Try recording from the DEFAULT mic and recognizing speech

If step 1 shows no devices, or shows devices but the default one (index
used automatically) isn't your real mic, that's the root cause.
"""

import speech_recognition as sr

print("=" * 50)
print("Available microphones on this system:")
print("=" * 50)
mic_list = sr.Microphone.list_microphone_names()
if not mic_list:
    print("⚠ NO microphones detected at all. Check Windows Sound settings")
    print("  (Settings > System > Sound > Input) — make sure a mic is")
    print("  connected AND set as default, and that mic privacy permissions")
    print("  are enabled for desktop apps.")
else:
    for i, name in enumerate(mic_list):
        print(f"  [{i}] {name}")

print()
print("=" * 50)
print("Testing default microphone (speak now)...")
print("=" * 50)

recognizer = sr.Recognizer()
try:
    with sr.Microphone() as source:
        print("Adjusting for ambient noise... (stay quiet for 1 sec)")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Listening... say something!")
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)

    print("Recognizing...")
    text = recognizer.recognize_google(audio)
    print(f"✅ SUCCESS — heard: \"{text}\"")

except Exception as e:
    print(f"❌ FAILED: {type(e).__name__}: {e}")
    print()
    print("If this failed but microphones WERE listed above, try setting")
    print("device_index explicitly, e.g.:")
    print("    sr.Microphone(device_index=1)")
    print("using the index number from the list above that matches your mic.") 
    