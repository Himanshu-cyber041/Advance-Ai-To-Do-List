"""
voice_handler.py
-----------------
  1. listen()  - microphone -> text
  2. speak()   - text -> speech (non-blocking)
Language, speech rate and microphone come from Settings (config.py),
so changes apply instantly without restarting.
"""

import threading

import config


class VoiceError(Exception):
    """Mic / speech service problem (not 'no speech detected')."""


class VoiceHandler:
    def __init__(self, device_index=None):
        self.device_index = device_index
        self._tts_lock = threading.Lock()
        self._recognizer = None

    def _rec(self):
        if self._recognizer is None:
            import speech_recognition as sr
            self._recognizer = sr.Recognizer()
        return self._recognizer

    # ------------------------------------------------------------------ #
    def listen(self, timeout=6, phrase_time_limit=12) -> str:
        try:
            import speech_recognition as sr
        except Exception as e:
            raise VoiceError(f"SpeechRecognition not installed: {e}")
        rec = self._rec()
        try:
            with sr.Microphone(device_index=self.device_index) as source:
                rec.adjust_for_ambient_noise(source, duration=0.5)
                audio = rec.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        except sr.WaitTimeoutError:
            return ""
        except Exception as e:
            raise VoiceError(f"Microphone error ({type(e).__name__}: {e}). "
                             "Pick your mic in Settings, or run test_mic.py.")
        try:
            return rec.recognize_google(audio, language=config.get_setting("voice_language"))
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            raise VoiceError(f"Speech service error (internet?): {e}")

    # ------------------------------------------------------------------ #
    def speak(self, text: str):
        def _run():
            with self._tts_lock:
                try:
                    import pyttsx3
                    engine = pyttsx3.init()
                    engine.setProperty("rate", int(config.get_setting("tts_rate")))
                    engine.say(text)
                    engine.runAndWait()
                    engine.stop()
                except Exception as e:
                    print(f"[voice] speak failed: {e}")

        threading.Thread(target=_run, daemon=True).start()

    @staticmethod
    def list_microphones() -> list:
        try:
            import speech_recognition as sr
            return sr.Microphone.list_microphone_names()
        except Exception:
            return []
