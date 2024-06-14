import os
import glob
import nltk
import speech_recognition as sr
from pydub import AudioSegment
from pydub.utils import make_chunks
import re
import psutil
import time

nltk.download('punkt')

def print_system_usage():
    usage = {
        'cpu_percent': psutil.cpu_percent(),
        'memory_percent': psutil.virtual_memory().percent,
        'available_memory_mb': psutil.virtual_memory().available / (1024 ** 2)
    }
    print(f"CPU Usage: {usage['cpu_percent']}%")
    print(f"Memory Usage: {usage['memory_percent']}%")
    print(f"Available Memory: {usage['available_memory_mb']} MB")
    return usage

def split_text_into_sentences(text):
    return nltk.sent_tokenize(text)

def split_text_into_chapters(text, chapter_pattern=r'\b\d+\b'):
    chapters = re.split(chapter_pattern, text)
    chapter_titles = re.findall(chapter_pattern, text)
    
    # Ensure the first chapter doesn't get missed if it starts right at the beginning
    if not chapters[0].strip():
        chapters.pop(0)
    
    if len(chapter_titles) != len(chapters):
        print(f"Warning: Found {len(chapter_titles)} chapter titles but {len(chapters)} chapters.")
    
    # Re-add the chapter titles as the first line of each chapter
    chapters = [chapter_titles[i] + "\n" + chapters[i] for i in range(min(len(chapter_titles), len(chapters)))]
    return chapters

def transcribe_audio(audio_file):
    recognizer = sr.Recognizer()
    
    try:
        # Ensure the file is treated as a recognized format
        print(f"Processing audio file: {audio_file}")
        if audio_file.endswith('.m4b'):
            audio = AudioSegment.from_file(audio_file, format="mp4")
        else:
            audio = AudioSegment.from_file(audio_file)
        
        chunks = make_chunks(audio, 2000)  # Split audio into smaller chunks of 2 seconds
        print(f"Audio file split into {len(chunks)} chunks")
        
        transcripts = []
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i + 1}/{len(chunks)}")
            chunk.export("temp.wav", format="wav")
            with sr.AudioFile("temp.wav") as source:
                audio_listened = recognizer.listen(source)
                try:
                    text = recognizer.recognize_google(audio_listened, language='ja')
                    transcripts.append(text)
                except sr.UnknownValueError:
                    print("Google Speech Recognition could not understand audio")
                except sr.RequestError as e:
                    print(f"Could not request results from Google Speech Recognition service; {e}")
            usage = print_system_usage()  # Print system usage after processing each chunk
            # Log detailed usage
            with open("resource_usage.log", "a") as log_file:
                log_file.write(f"Chunk {i + 1}/{len(chunks)} - {time.ctime()}: {usage}\n")

        return " ".join(transcripts)
    except Exception as e:
        print(f"Error processing audio file: {e}")
        return ""

def align_text_with_audio(sentences, transcript):
    words = transcript.split()
    current_time = 0
    word_index = 0

    subtitles = []
    for sentence in sentences:
        words_in_sentence = sentence.split()
        start_time = None

        while word_index < len(words):
            if re.sub(r'\W+', '', words[word_index]) in words_in_sentence:
                if start_time is None:
                    start_time = current_time
                word_index += 1
                current_time += 1000  # Adjust based on average word length in ms
            else:
                word_index += 1
                current_time += 1000  # Adjust based on average word length in ms

            if word_index >= len(words_in_sentence):
                subtitles.append((start_time, current_time, sentence))
                break

    return subtitles

def generate_srt(subtitles, output_file):
    with open(output_file, 'w') as f:
        for i, (start_time, end_time, sentence) in enumerate(subtitles):
            start_time_str = format_time(start_time)
            end_time_str = format_time(end_time)
            f.write(f"{i+1}\n{start_time_str} --> {end_time_str}\n{sentence}\n\n")

def format_time(ms):
    hours = ms // (3600 * 1000)
    ms %= (3600 * 1000)
    minutes = ms // (60 * 1000)
    ms %= (60 * 1000)
    seconds = ms // 1000
    ms %= 1000
    return f"{hours:02}:{minutes:02}:{seconds:02},{ms:03}"

def find_files(extension):
    return glob.glob(f"*.{extension}")

# Main
text_files = find_files("txt")
audio_files = find_files("m4b")

if not text_files or not audio_files:
    print("No text or audio files found in the directory.")
    exit(1)

for text_file, audio_file in zip(text_files, audio_files):
    output_file_base = os.path.splitext(text_file)[0]

    with open(text_file, 'r', encoding='utf-8') as f:
        text = f.read()

    # Split text into chapters
    chapters = split_text_into_chapters(text)

    # Process each chapter separately
    for i, chapter in enumerate(chapters):
        print(f"Processing Chapter {i + 1}")
        sentences = split_text_into_sentences(chapter)
        print_system_usage()  # Print system usage before processing each chapter
        transcript = transcribe_audio(audio_file)  # Assuming the audio covers all chapters
        print_system_usage()  # Print system usage after processing each chapter
        subtitles = align_text_with_audio(sentences, transcript)
        output_file = f"{output_file_base}_chapter_{i+1}.srt"
        generate_srt(subtitles, output_file)
        print(f"Subtitles for Chapter {i+1} saved to {output_file}")
