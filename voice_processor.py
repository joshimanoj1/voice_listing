# voice_processor.py
import speech_recognition as sr
import pyaudio
import wave
import os
import time

def record_audio(output_file="temp_audio.wav", duration=10):
    """Record audio from the microphone for a given duration."""
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    print(f"Recording for {duration} seconds... Speak now!")
    frames = []
    start_time = time.time()

    # Calculate expected iterations
    expected_iterations = int((RATE * duration) / CHUNK)
    for i in range(expected_iterations):
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
        except IOError as e:
            print(f"Warning: {e} - Continuing recording...")

    end_time = time.time()
    actual_duration = end_time - start_time
    print(f"Recording finished. Actual duration: {actual_duration:.2f} seconds")

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(output_file, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    return output_file

def speech_to_text(audio_file, language="hi-IN"):
    """Convert audio file to text using Google Speech Recognition."""
    recognizer = sr.Recognizer()

    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio, language=language)
        return text
    except sr.UnknownValueError:
        return "Could not understand the audio."
    except sr.RequestError as e:
        return f"Error with speech recognition service: {e}"

def get_product_description(anguage="hi-IN"):
    """Record audio and return the Hindi description as text."""
    audio_file = record_audio()
    description = speech_to_text(audio_file)
    if os.path.exists(audio_file):
        os.remove(audio_file)  # Clean up temporary file
    return description