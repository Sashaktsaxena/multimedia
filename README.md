# 🖐️ Gesture-Controlled Video Player

A modern Spotify-like media player that uses your hand gestures to control video playback. Built with Python and featuring real-time hand tracking via MediaPipe, this player offers an intuitive and hands-free way to control your media.

## 🎥 Features

### Gesture Controls
| Gesture         | Action                  |
|----------------|--------------------------|
| ✋ Open palm     | Play                     |
| ✊ Fist          | Pause                    |
| ☝️ Index only    | Forward 2 seconds        |
| � Thumb only    | Rewind 2 seconds         |
| ✌️ Peace sign    | Mute toggle             |
| � Rock sign     | Restart video           |

### Modern UI Features
- Spotify-inspired dark theme
- Progress bar for video timeline
- Play/Pause and Mute/Unmute buttons
- Real-time gesture preview window
- On-screen gesture instructions

## 🛠️ Tech Stack

- Python
- OpenCV (Video processing)
- MediaPipe (Hand tracking)
- CustomTkinter (Modern UI)
- Pillow (Image processing)

## � Getting Started

1. **Install Requirements:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Place Your Video:**
   - Put your video file in the project directory
   - Rename it to 'your_video.mp4' or update the video path in main.py

3. **Run the Player:**
   ```bash
   python main.py
   ```

## 🎮 Usage

1. Launch the player
2. Allow webcam access
3. Hold your hand up in front of the camera
4. Use the gestures shown in the instructions to control playback
5. Click the on-screen buttons for traditional controls
6. Press 'Q' to quit

## 📝 Requirements

- Python 3.8+
- Webcam
- Internet connection (for initial MediaPipe model download)
