import os
import cv2
import mediapipe as mp
import time
import customtkinter as ctk
from PIL import Image, ImageTk
import threading
from tkinter import Canvas, filedialog, messagebox
import numpy as np
import sounddevice as sd


# Setup MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

# Setup theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Create main window
class MediaPlayer(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gesture Media Player")
        self.geometry("1200x800")

        # Create main container with two columns
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Left column for video and controls
        self.left_column = ctk.CTkFrame(self.container)
        self.left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Right column for gesture control
        self.right_column = ctk.CTkFrame(self.container)
        self.right_column.pack(side="right", fill="y", padx=(10, 0))

        # Video frame in left column
        self.video_frame = ctk.CTkFrame(self.left_column)
        self.video_frame.pack(fill="both", expand=True)
        
        # Controls frame in left column
        self.controls_frame = ctk.CTkFrame(self.left_column, height=120)
        self.controls_frame.pack(fill="x", pady=(20, 0))
        
        # Gesture frame in right column
        self.gesture_frame = ctk.CTkFrame(self.right_column)
        self.gesture_frame.pack(fill="both", expand=True)

        # Title
        self.title_label = ctk.CTkLabel(
            self.gesture_frame,
            text="Gesture Controls",
            font=("Helvetica", 16, "bold")
        )
        self.title_label.pack(pady=(10, 5))

        # Add gesture instructions with improved formatting
        self.instructions = ctk.CTkLabel(
            self.gesture_frame,
            text="\n".join([
                "✋ Open Palm - Play",
                "✊ Closed Fist - Pause",
                "☝️ Index Finger - Forward",
                "👍 Thumb - Rewind",
                "✌️ Peace Sign - Mute/Unmute",
                "🤘 Rock Sign - Restart",
                "👉 Three Up (Index+Middle+Ring) - Next",
                "👈 Last Three Up (Middle+Ring+Pinky) - Previous",
            ]),
            justify="left",
            font=("Helvetica", 12)
        )
        self.instructions.pack(pady=10)

        # Gesture view with 4:3 aspect ratio for better hand tracking
        self.gesture_canvas = Canvas(self.gesture_frame, width=320, height=240, bg="black")
        self.gesture_canvas.pack(pady=10, padx=10)

        # Current gesture display
        self.current_gesture_label = ctk.CTkLabel(
            self.gesture_frame,
            text="Current Gesture: None",
            font=("Helvetica", 14, "bold"),
            text_color="#00FF00"
        )
        self.current_gesture_label.pack(pady=10)

        # Finger status display
        self.finger_status_label = ctk.CTkLabel(
            self.gesture_frame,
            text="Fingers: - - - - -",
            font=("Helvetica", 12),
            text_color="#FFAA00"
        )
        self.finger_status_label.pack(pady=5)

        # Playlist UI
        ctk.CTkLabel(self.gesture_frame, text="Playlist", font=("Helvetica", 14, "bold")).pack(pady=(10, 5))
        self.playlist_frame = ctk.CTkScrollableFrame(self.gesture_frame, width=280, height=200)
        self.playlist_frame.pack(padx=10, pady=5, fill="x")
        self.playlist_item_buttons = []

        pl_btns = ctk.CTkFrame(self.gesture_frame)
        pl_btns.pack(pady=5)
        self.add_playlist_btn = ctk.CTkButton(pl_btns, text="➕ Add to Playlist", command=self.add_to_playlist, width=150)
        self.add_playlist_btn.pack(side="left", padx=5)
        self.prev_btn = ctk.CTkButton(pl_btns, text="⏮ Prev", command=lambda: self.play_previous(auto=False), width=70)
        self.prev_btn.pack(side="left", padx=5)
        self.next_btn = ctk.CTkButton(pl_btns, text="⏭ Next", command=lambda: self.play_next(auto=False), width=70)
        self.next_btn.pack(side="left", padx=5)

        # Video canvas with 16:9 aspect ratio
        self.video_canvas = Canvas(self.video_frame, bg="black", width=960, height=540)
        self.video_canvas.pack(pady=10, padx=10, fill="both", expand=True)

        # Video file label
        self.video_file_label = ctk.CTkLabel(
            self.controls_frame,
            text="No video loaded",
            font=("Helvetica", 10),
            text_color="gray"
        )
        self.video_file_label.pack(pady=(5, 0))

        # Time display
        self.time_frame = ctk.CTkFrame(self.controls_frame)
        self.time_frame.pack(fill="x", padx=10, pady=(5, 5))
        
        self.time_label = ctk.CTkLabel(self.time_frame, text="0:00 / 0:00")
        self.time_label.pack(side="right")

        # Progress bar with click handling
        self.progress_frame = ctk.CTkFrame(self.controls_frame)
        self.progress_frame.pack(fill="x", padx=10, pady=5)
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)
        self.progress_bar.bind("<Button-1>", self.seek_video)

        # Control buttons with improved layout
        self.button_frame = ctk.CTkFrame(self.controls_frame)
        self.button_frame.pack(fill="x", padx=10, pady=5)

        # Left side controls
        self.left_controls = ctk.CTkFrame(self.button_frame)
        self.left_controls.pack(side="left")

        # Add Load Video button
        self.load_button = ctk.CTkButton(
            self.left_controls, 
            text="📁 Load Video", 
            width=100, 
            command=self.load_video
        )
        self.load_button.pack(side="left", padx=5)

        self.play_button = ctk.CTkButton(
            self.left_controls, 
            text="Play", 
            width=80, 
            command=self.toggle_play,
            state="disabled"
        )
        self.play_button.pack(side="left", padx=5)

        self.mute_button = ctk.CTkButton(
            self.left_controls, 
            text="Mute", 
            width=80, 
            command=self.toggle_mute,
            state="disabled"
        )
        self.mute_button.pack(side="left", padx=5)

        # Right side volume control
        self.right_controls = ctk.CTkFrame(self.button_frame)
        self.right_controls.pack(side="right")

        ctk.CTkLabel(self.right_controls, text="Volume:").pack(side="left", padx=5)
        self.volume_slider = ctk.CTkSlider(self.right_controls, from_=0, to=100, width=100)
        self.volume_slider.pack(side="right", padx=5)
        self.volume_slider.set(100)

        # Initialize video capture as None
        self.video = None
        self.video_loaded = False

        # Playlist state
        self.playlist = []
        self.current_index = -1

        # Start webcam
        self.cam = cv2.VideoCapture(0)
        if not self.cam.isOpened():
            messagebox.showerror("Camera Error", "Cannot access webcam.")
            self.destroy()
            return

        # State variables
        self.playing = False
        self.muted = False
        self.last_gesture = None
        self.last_time = time.time()
        self.gesture_cooldown = 1.2  # seconds
        self.running = True

        # REMOVE thread; use main-thread after loop instead
        # self.video_thread = threading.Thread(target=self.update_frames, daemon=True)
        # self.video_thread.start()
        self.after(16, self.update_frames)  # ~60 FPS update on main thread

    # ===== Playlist helpers =====
    def render_playlist(self):
        # Clear UI
        for w in self.playlist_item_buttons:
            w.destroy()
        self.playlist_item_buttons.clear()

        # Rebuild
        for i, path in enumerate(self.playlist):
            name = os.path.basename(path)
            is_current = (i == self.current_index)
            btn = ctk.CTkButton(
                self.playlist_frame,
                text=("▶ " if is_current else "   ") + name,
                # anchor removed; CTkButton doesn't support 'anchor'
                width=250,
                command=lambda idx=i: self.load_from_playlist(idx)
            )
            if is_current:
                btn.configure(fg_color="#1F6AA5")
            btn.pack(fill="x", padx=5, pady=2)
            self.playlist_item_buttons.append(btn)

    def add_to_playlist(self):
        files = filedialog.askopenfilenames(
            title="Add Videos to Playlist",
            filetypes=[("Video Files", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm"), ("All Files", "*")]
        )
        if not files:
            return
        # Extend playlist (avoid duplicates)
        for f in files:
            if f not in self.playlist:
                self.playlist.append(f)
        # Autoload first if nothing loaded yet
        if self.current_index == -1 and self.playlist:
            self.load_from_playlist(0)
        self.render_playlist()

    def load_from_playlist(self, index: int):
        if index < 0 or index >= len(self.playlist):
            return
        self.current_index = index
        self.load_video_file(self.playlist[index], announce=False)
        self.playing = True
        self.play_button.configure(text="Pause")
        self.render_playlist()

    def play_next(self, auto=True):
        if not self.playlist:
            return
        nxt = self.current_index + 1
        if nxt >= len(self.playlist):
            if auto:
                # Stop at end of playlist
                self.playing = False
                self.play_button.configure(text="Play")
                return
            else:
                nxt = 0
        self.load_from_playlist(nxt)

    def play_previous(self, auto=False):
        if not self.playlist:
            return
        prv = self.current_index - 1
        if prv < 0:
            if auto:
                return
            else:
                prv = len(self.playlist) - 1
        self.load_from_playlist(prv)

    # ===== Load video =====
    def load_video(self):
        file_path = filedialog.askopenfilename(
            title="Select a Video File",
            filetypes=[
                ("Video Files", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm"),
                ("MP4 Files", "*.mp4"),
                ("AVI Files", "*.avi"),
                ("All Files", "*.*")
            ]
        )
        if file_path:
            # If using playlist, update current index accordingly
            if file_path not in self.playlist:
                self.playlist.append(file_path)
            self.current_index = self.playlist.index(file_path)
            self.load_video_file(file_path, announce=True)
            self.render_playlist()

    def load_video_file(self, file_path: str, announce: bool = True):
        # Release previous video if any
        if self.video is not None:
            self.video.release()
        
        # Load new video
        self.video = cv2.VideoCapture(file_path)
        
        if not self.video.isOpened():
            messagebox.showerror("Error", "Cannot open video file.")
            self.video = None
            self.video_loaded = False
            return
        
        self.video_loaded = True
        self.playing = False
        
        # Update UI
        filename = os.path.basename(file_path)
        self.video_file_label.configure(text=f"📹 {filename}", text_color="white")
        self.play_button.configure(state="normal", text="Play")
        self.mute_button.configure(state="normal")
        
        # Reset progress
        self.progress_bar.set(0)
        
        # Get video info
        total_frames = self.video.get(cv2.CAP_PROP_FRAME_COUNT)
        fps = self.video.get(cv2.CAP_PROP_FPS)
        total_time = total_frames / fps if fps and fps > 0 else 0
        self.time_label.configure(text=f"0:00 / {self.format_time(total_time)}")

        if announce:
            messagebox.showinfo("Success", f"Video loaded successfully!\n{filename}")

    # ===== Utils and playback controls =====
    def get_fingers_up(self, hand):
        tip_ids = [4, 8, 12, 16, 20]
        fingers = []
        # Thumb: left/right
        fingers.append(1 if hand.landmark[4].x < hand.landmark[3].x else 0)
        # Other fingers: up/down
        for tip in tip_ids[1:]:
            fingers.append(1 if hand.landmark[tip].y < hand.landmark[tip - 2].y else 0)
        return fingers

    def format_time(self, seconds):
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"

    def seek_video(self, event):
        if not self.video_loaded or self.video is None:
            return
        click_x = event.x
        bar_width = self.progress_bar.winfo_width()
        if bar_width <= 0:
            return
        ratio = max(0.0, min(1.0, click_x / bar_width))
        total_frames = self.video.get(cv2.CAP_PROP_FRAME_COUNT)
        target_frame = int(total_frames * ratio)
        self.video.set(cv2.CAP_PROP_POS_FRAMES, target_frame)

    def toggle_play(self):
        if not self.video_loaded:
            messagebox.showwarning("No Video", "Please load a video first!")
            return
        self.playing = not self.playing
        self.play_button.configure(text="Pause" if self.playing else "Play")

    def toggle_mute(self):
        self.muted = not self.muted
        self.mute_button.configure(text="Unmute" if self.muted else "Mute")
        if self.muted:
            self.volume_slider.set(0)
        else:
            self.volume_slider.set(100)

    def get_gesture_name(self, fingers):
        """
        Map finger patterns to actions:
        [Thumb, Index, Middle, Ring, Pinky]
        """
        if fingers == [0, 1, 1, 1, 1]:
            return "✋ PLAY", "play"
        elif fingers == [0, 0, 0, 0, 0]:
            return "✊ PAUSE", "pause"
        elif fingers == [0, 1, 0, 0, 0]:
            return "☝️ FORWARD", "forward"
        elif fingers == [1, 0, 0, 0, 0]:
            return "👍 REWIND", "rewind"
        elif fingers == [0, 1, 1, 0, 0]:
            return "✌️ MUTE/UNMUTE", "mute"
        elif fingers == [0, 1, 0, 0, 1]:
            return "🤘 RESTART", "restart"
        elif fingers == [0, 1, 1, 1, 0]:
            return "⏭ NEXT", "next"         # Index+Middle+Ring up
        elif fingers == [0, 0, 1, 1, 1]:
            return "⏮ PREVIOUS", "previous" # Middle+Ring+Pinky up
        else:
            return "❓ UNKNOWN", None

    def update_frames(self):
        if not self.running:
            return
        try:
            # Read webcam
            ret_cam, cam_frame = self.cam.read()
            if ret_cam:
                cam_frame = cv2.flip(cam_frame, 1)
                cam_rgb = cv2.cvtColor(cam_frame, cv2.COLOR_BGR2RGB)
                results = hands.process(cam_rgb)

                # Detect gesture
                gesture = None
                gesture_display = "None"
                finger_status = "- - - - -"

                if results and results.multi_hand_landmarks:
                    for handLms in results.multi_hand_landmarks:
                        mp_draw.draw_landmarks(cam_frame, handLms, mp_hands.HAND_CONNECTIONS)
                        fingers = self.get_fingers_up(handLms)
                        finger_names = ["👍", "☝️", "🖕", "💍", "🤙"]
                        finger_status = " ".join([finger_names[i] if fingers[i] == 1 else "✖" for i in range(5)])
                        gesture_display, gesture = self.get_gesture_name(fingers)

                # Update gesture labels (main thread safe)
                self.current_gesture_label.configure(text=f"Current Gesture: {gesture_display}")
                self.finger_status_label.configure(text=f"Fingers: {finger_status}")

                # Trigger gesture if cooldown passed
                current_time = time.time()
                if gesture and self.video_loaded and (gesture != self.last_gesture or current_time - self.last_time > self.gesture_cooldown):
                    fps = self.video.get(cv2.CAP_PROP_FPS) if self.video else 0
                    pos = self.video.get(cv2.CAP_PROP_POS_FRAMES) if self.video else 0

                    if gesture == "play":
                        self.playing = True
                        self.play_button.configure(text="Pause")
                    elif gesture == "pause":
                        self.playing = False
                        self.play_button.configure(text="Play")
                    elif gesture == "forward" and self.video:
                        self.video.set(cv2.CAP_PROP_POS_FRAMES, pos + int(fps * 2))
                    elif gesture == "rewind" and self.video:
                        self.video.set(cv2.CAP_PROP_POS_FRAMES, max(0, pos - int(fps * 2)))
                    elif gesture == "mute":
                        self.muted = not self.muted
                        self.mute_button.configure(text="Unmute" if self.muted else "Mute")
                    elif gesture == "restart" and self.video:
                        self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        self.video.read()
                        self.playing = True
                        self.play_button.configure(text="Pause")
                    elif gesture == "next":
                        self.play_next(auto=False)
                    elif gesture == "previous":
                        self.play_previous(auto=False)

                    self.last_gesture = gesture
                    self.last_time = current_time

                # Draw gesture camera
                cam_frame = cv2.cvtColor(cam_frame, cv2.COLOR_BGR2RGB)
                cam_frame = cv2.resize(cam_frame, (320, 240))
                cam_photo = ImageTk.PhotoImage(Image.fromarray(cam_frame))
                self.gesture_canvas.create_image(0, 0, anchor="nw", image=cam_photo)
                self.gesture_canvas.image = cam_photo

            # Update video playback
            if self.playing and self.video_loaded and self.video is not None:
                ret_vid, frame = self.video.read()
                if ret_vid:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    # Fit to canvas while preserving aspect ratio
                    video_ratio = frame.shape[1] / frame.shape[0]
                    canvas_width = max(1, self.video_canvas.winfo_width())
                    canvas_height = max(1, self.video_canvas.winfo_height())
                    canvas_ratio = canvas_width / canvas_height

                    if video_ratio > canvas_ratio:
                        new_width = canvas_width
                        new_height = int(canvas_width / video_ratio)
                    else:
                        new_height = canvas_height
                        new_width = int(canvas_height * video_ratio)
                    frame = cv2.resize(frame, (new_width, new_height))

                    # Visual indicator for mute/low volume
                    volume = 0 if self.muted else self.volume_slider.get() / 100
                    if volume < 0.1:
                        frame = cv2.convertScaleAbs(frame, alpha=0.7)

                    video_photo = ImageTk.PhotoImage(Image.fromarray(frame))
                    x = (canvas_width - new_width) // 2
                    y = (canvas_height - new_height) // 2
                    self.video_canvas.create_image(x, y, anchor="nw", image=video_photo)
                    self.video_canvas.image = video_photo

                    # Progress/time
                    total_frames = self.video.get(cv2.CAP_PROP_FRAME_COUNT)
                    current_frame = self.video.get(cv2.CAP_PROP_POS_FRAMES)
                    fps = self.video.get(cv2.CAP_PROP_FPS)
                    if total_frames > 0 and fps and fps > 0:
                        self.progress_bar.set(current_frame / total_frames)
                        current_time_sec = current_frame / fps
                        total_time = total_frames / fps
                        self.time_label.configure(
                            text=f"{self.format_time(current_time_sec)} / {self.format_time(total_time)}"
                        )
                else:
                    # Auto next at end
                    self.play_next(auto=True)
        except Exception as e:
            print(f"Error in update_frames: {e}")
        finally:
            if self.running:
                self.after(16, self.update_frames)  # schedule next tick

    def cleanup(self):
        self.running = False
        # Give pending after a moment to stop naturally
        time.sleep(0.1)
        if self.cam:
            self.cam.release()
        if self.video:
            self.video.release()
        cv2.destroyAllWindows()
        self.quit()

if __name__ == "__main__":
    app = MediaPlayer()
    app.protocol("WM_DELETE_WINDOW", app.cleanup)
    app.mainloop()


