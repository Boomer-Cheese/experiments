from pathlib import Path
import click
from moviepy.editor import VideoFileClip
from PIL import Image  # For saving frames properly
from pytubefix import YouTube  # Import pytube to download YouTube videos
from pytubefix.cli import on_progress
import shutil

@click.command()
@click.option("--path", default="video.mp4", help="Path to video file or YouTube URL", type=str)
@click.option("--perc-frames", default=0.10, help="Percentage of frames to use for colmap", type=float)
@click.option("--max-frames", default=180, help="Max number of frames to use for colmap", type=int)
def main(path, perc_frames, max_frames):
    """
    Process a video file or YouTube URL to extract a subset of frames for use with COLMAP.

    Args:
        path (str): Path to the input video file or YouTube URL.
        perc_frames (float): Percentage of frames to use for extraction.
    """
    # Check if the path is a YouTube URL or a local file
    if path.startswith("http://") or path.startswith("https://"):
        # If the path is a YouTube URL, download the video using pytube
        try:
            print("Downloading video from YouTube...")
            yt = YouTube(path, on_progress_callback=on_progress)
            
            # Filter streams by MP4 format
            video_streams = yt.streams.filter(file_extension="mp4")

            if not video_streams:
                print("Error: No suitable MP4 video stream found.")
                return

            # Select the highest resolution video stream
            video_stream = video_streams.get_highest_resolution()
            
            # Download the video
            video_path = Path("downloaded_video")
            video_stream.download(output_path=video_path.parent, filename=video_path.name)
            print(f"Downloaded video to {video_path}")
            path = video_path.with_suffix(".mp4")
        except Exception as e:
            print(f"Error downloading video: {e}")
            return
    else:
        # Check if the path is a valid local file
        path = Path(path)
        if not path.exists():
            print("Error: File does not exist.")
            return

    # Open the video file using MoviePy
    clip = VideoFileClip(str(path))
    total_frames = int(clip.fps * clip.duration)

    # Ensure perc_frames is valid
    if not (0 < perc_frames <= 1):
        print("Error: perc_frames must be between 0 and 1.")
        return

    # Create output directory for images
    output_dir = path.parent / "images"
    shutil.rmtree(output_dir)
    output_dir.mkdir()

    # Calculate the frame step based on the percentage
    frame_step = max(1, int(1 / perc_frames))
    frame_indices = range(0, total_frames, frame_step)[:max_frames]

    print(f"Extracting frames to {output_dir}...")

    # Extract and save frames
    for fnum in frame_indices:
        frame_time = fnum / clip.fps  # Convert frame index to time
        frame_image = clip.get_frame(frame_time)  # NumPy array in (height, width, channels)

        # Convert to PIL image to ensure correct handling of dimensions
        frame_image_pil = Image.fromarray(frame_image)
        target = output_dir / f"{fnum}.jpg"
        frame_image_pil.save(str(target))

    print(f"Frame extraction complete. {len(frame_indices)} frames saved in {output_dir}.")


if __name__ == "__main__":
    main()

