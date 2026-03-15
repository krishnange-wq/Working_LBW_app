# New MoviePy 2.0+ Import Style
from moviepy import VideoFileClip, vfx


def mirror_4k_video(input_path, output_path):
    # Load the 4K .mov
    clip = VideoFileClip(input_path)

    # In v2.0, you can use .mirrored("x") or call vfx directly
    # This keeps your high-fidelity 4K audio intact
    flipped_clip = clip.with_effects([vfx.MirrorX()])

    # Write result - ensuring lowercase .mov as per your preference
    flipped_clip.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="temp-audio.m4a",
        remove_temp=True,
        fps=clip.fps
    )

    clip.close()
    flipped_clip.close()


if __name__ == "__main__":
    # Test with your mirrored file name
    mirror_4k_video("IMG_6963.mov", "mirrored_4k_test.mov")
