import cv2
import argparse
import os


def get_readable_frame_count(video_path):
    """
    Count the actual number of frames that OpenCV can decode.
    This avoids relying on incorrect video metadata.
    """
    capture = cv2.VideoCapture(video_path)

    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    count = 0

    while True:
        success, frame = capture.read()

        if not success:
            break

        count += 1

    capture.release()

    return count


def extract_frames(video_path, output_dir, num_frames):
    os.makedirs(output_dir, exist_ok=True)

    print("Checking actual readable frames...")
    readable_frames = get_readable_frame_count(video_path)

    print(f"Actual readable frames: {readable_frames}")

    if readable_frames == 0:
        raise RuntimeError("No readable frames found in the video.")

    if num_frames > readable_frames:
        print(
            f"Requested {num_frames} frames, "
            f"but only {readable_frames} are readable."
        )
        num_frames = readable_frames

    # Select evenly spaced readable frame numbers.
    if num_frames == 1:
        frame_indices = [0]
    else:
        frame_indices = [
            round(i * (readable_frames - 1) / (num_frames - 1))
            for i in range(num_frames)
        ]

    capture = cv2.VideoCapture(video_path)

    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    saved_count = 0

    for frame_index in frame_indices:

        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)

        success, frame = capture.read()

        if not success:
            print(f"WARNING: Could not read frame {frame_index}")
            continue

        output_path = os.path.join(
            output_dir,
            f"frame_{frame_index:05d}.jpg"
        )

        cv2.imwrite(output_path, frame)

        saved_count += 1

        print(
            f"Saved frame {frame_index}: "
            f"{output_path}"
        )

    capture.release()

    print()
    print("=" * 60)
    print("GROUND-TRUTH FRAME EXTRACTION COMPLETE")
    print("=" * 60)
    print(f"Actual readable frames: {readable_frames}")
    print(f"Requested frames:       {num_frames}")
    print(f"Saved frames:            {saved_count}")
    print(f"Output:                  {output_dir}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Extract readable frames for ground-truth annotation."
    )

    parser.add_argument(
        "--video",
        required=True,
        help="Path to input video"
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Output directory for extracted frames"
    )

    parser.add_argument(
        "--num-frames",
        type=int,
        default=30,
        help="Number of frames to extract"
    )

    args = parser.parse_args()

    extract_frames(
        args.video,
        args.output,
        args.num_frames
    )


if __name__ == "__main__":
    main()