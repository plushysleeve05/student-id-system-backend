# test_pipeline.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import asyncio
from match_faces import detect_and_match

if __name__ == "__main__":
    video_path = "/home/ayombalima/video_uploads/c0rzMtFm9ms0FbH4BzWkRN-4k5d8d7i1TVakO62yM5c=_plaintext_638016421337507220.mp4"
    asyncio.run(detect_and_match(video_path, mode="ml"))  # or "matching"
