import elevenlabs
from elevenlabs.api import VoiceSettings
import requests
from datetime import datetime 
import os
import logging

import pyaudio
import wave
import time
import speech_recognition as sr

API_KEY = "45ed85b5f77fac627a018b97dce4cdca"
FS = 44100  # Sample rate
elevenlabs.set_api_key(API_KEY)
logging.basicConfig(level=logging.INFO)
TRIGGER_KEYWORD = "realm of curiosity"

def _record(record_seconds, filename):
    chunk = 1024
    FORMAT = pyaudio.paInt16
    channels = 1
    sample_rate = 44100
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=channels,
                    rate=sample_rate,
                    input=True,
                    output=True,
                    frames_per_buffer=chunk)
    frames = []
    for i in range(int(sample_rate / chunk * record_seconds)):
        data = stream.read(chunk)
        frames.append(data)
    stream.stop_stream()
    stream.close()
    p.terminate()        
    wf = wave.open(filename, "wb")
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(sample_rate)
    wf.writeframes(b"".join(frames))
    wf.close()

class Voice:
    def __init__(self, base_voice_id):
        logging.info("Initializing Voice")

        self.initial_time = datetime.now()
        self.voice_id = f"{base_voice_id}-{self.initial_time.strftime('%m%d-%H:%M')}"
        self.voice_files = []
    
    def record(self, num_seconds=15):
        logging.info("Recording Voice")
        today_date = self.initial_time.strftime("%Y-%m-%d")
        save_dir = f'./voices/{today_date}'
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        recorded_time = datetime.now().strftime("%M:%S")
        save_path = f'{save_dir}/{self.voice_id}-rec{recorded_time}.wav'
        _record(num_seconds, save_path)
        self.voice_files.append(save_path)
        logging.info("Finished Recording Voice")
        return self.voice_files

    def clone(self):
        logging.info("Cloning Voice")

        voice = elevenlabs.clone(
            name=self.voice_id,
            description=f"Cloned Mismus Voice {self.voice_id} at {self.initial_time}",
            files=self.voice_files,
        )
        voice_settings = VoiceSettings(
            stability = 0.37,
            similarity_boost = 0.8,
            style = 0.05,
            use_speaker_boost = True
        )

        voice.edit(voice_settings=voice_settings)
        return voice

    def generate(self, text):
        logging.info("Generating Voice")
        
        audio = elevenlabs.generate(text=text, voice=self.voice_id)
        elevenlabs.play(audio)

        history = elevenlabs.api.History.from_api()
        print(history)


    def delete_saved_recordings(self):
        logging.info("Deleting Saved Recordings")
        for file in self.voice_files:
            os.remove(file)

    def delete_cloned_voice(self):
        logging.info("Deleting Voice")

        url = f"https://api.elevenlabs.io/v1/voices/{self.voice_id}"
        headers = {
        "Accept": "application/json",
        "xi-api-key": API_KEY
        }
        response = requests.delete(url, headers=headers)
        return response.text

    def cleanup(self):
        self.delete_saved_recordings()
        self.delete_cloned_voice()

def trigger_voice_clone():
    voice = Voice("mismus")
    voice.record(15)
    voice.clone()
    voice.generate("In meadows kissed by golden sun, A happy butterfly takes its run, With wings of colors, bright and gay, It dances through the light of day.")
    voice.cleanup()

if __name__ == "__main__":
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        while True:
            audio = r.listen(source, 10, 5)
            try:
                text = r.recognize_google(audio)
                logging.info(f"Heard Background Audio: {text}")
                if TRIGGER_KEYWORD in text.lower():
                    logging.info(f"Heard Trigger command {TRIGGER_KEYWORD}, starting voice clone.")
                    trigger_voice_clone()
            except LookupError:
                logging.info("Could not understand audio")

    try:
        print("You said " + r.recognize_google(audio))
    except LookupError:
        print("Could not understand audio")