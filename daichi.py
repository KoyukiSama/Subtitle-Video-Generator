import os
import subprocess
import glob

def split_audio_to_videos(input_file):
    output_dir = "vid"
    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.splitext(input_file)[0]

    # Split audio file by chapters using mkvmerge
    subprocess.run(["mkvmerge", "-o", "temp.mka", "--split", "chapters:all", input_file])

    # Convert each chapter to video with black background using ffmpeg
    for i, chapter_file in enumerate(os.listdir(".")):
        if chapter_file.endswith(".mka"):
            #base_name = os.path.splitext(chapter_file)[0]
            output_name = f"{base_name}-{i - 1:03d}.mp4"

            subprocess.run([
                "ffmpeg",
                "-f", "lavfi",
                "-i", "color=c=black:s=1280x720:r=5",
                "-i", chapter_file,
                "-crf", "0",
                "-c:a", "copy",
                "-sn",
                "-f", "mp4",
                "-shortest",
                os.path.join(output_dir, output_name)
            ])

    # Clean up temporary files
    for f in glob.glob("temp-*.mka"):
        os.remove(f)

if __name__ == "__main__":
    for audio_file in glob.glob("*.m4b"):
        split_audio_to_videos(audio_file)