import cv2
import mediapipe as mp
import time
import customtkinter as ctk
from PIL import Image, ImageTk
import threading
from tkinter import Canvas, filedialog, messagebox

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
                "🤘 Rock Sign - Restart"
            ]),
            justify="left",
            font=("Helvetica", 12)
        )
        self.instructions.pack(pady=10)

        # Gesture view with 4:3 aspect ratio for better hand tracking
        self.gesture_canvas = Canvas(self.gesture_frame, width=320, height=240, bg="black")
        self.gesture_canvas.pack(pady=10, padx=10)

        # Current gesture display - MOVED HERE
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
        self.gesture_cooldown = 1.5  # seconds
        self.running = True

        # Start video thread
        self.video_thread = threading.Thread(target=self.update_frames, daemon=True)
        self.video_thread.start()

    def load_video(self):
        """Open file dialog to select a video file"""
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
            import os
            filename = os.path.basename(file_path)
            self.video_file_label.configure(text=f"📹 {filename}", text_color="white")
            self.play_button.configure(state="normal", text="Play")
            self.mute_button.configure(state="normal")
            
            # Reset progress
            self.progress_bar.set(0)
            
            # Get video info
            total_frames = self.video.get(cv2.CAP_PROP_FRAME_COUNT)
            fps = self.video.get(cv2.CAP_PROP_FPS)
            total_time = total_frames / fps if fps > 0 else 0
            
            self.time_label.configure(text=f"0:00 / {self.format_time(total_time)}")
            
            messagebox.showinfo("Success", f"Video loaded successfully!\n{filename}")

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
        """Convert seconds to MM:SS format"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"

    def seek_video(self, event):
        """Handle click on progress bar to seek in video"""
        if not self.video_loaded or self.video is None:
            return
        # Calculate click position ratio
        click_x = event.x
        bar_width = self.progress_bar.winfo_width()
        if bar_width <= 0:
            return
        ratio = click_x / bar_width
        
        # Set video position
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
        # Apply volume
        if self.muted:
            self.volume_slider.set(0)
        else:
            self.volume_slider.set(100)

    def get_gesture_name(self, fingers):
        """Get gesture name and emoji from finger pattern"""
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
        else:
            return "❓ UNKNOWN", None

    def update_frames(self):
        while self.running:
            try:
                # Read webcam
                ret_cam, cam_frame = self.cam.read()
                if not ret_cam:
                    break
                cam_frame = cv2.flip(cam_frame, 1)
                cam_rgb = cv2.cvtColor(cam_frame, cv2.COLOR_BGR2RGB)
                results = hands.process(cam_rgb)

                # Detect gesture
                gesture = None
                gesture_display = "None"
                finger_status = "- - - - -"
                
                if results.multi_hand_landmarks:
                    for handLms in results.multi_hand_landmarks:
                        mp_draw.draw_landmarks(cam_frame, handLms, mp_hands.HAND_CONNECTIONS)
                        fingers = self.get_fingers_up(handLms)
                        
                        # Update finger status display
                        finger_names = ["👍", "☝️", "🖕", "💍", "🤙"]
                        finger_status = " ".join([finger_names[i] if fingers[i] == 1 else "✖" for i in range(5)])
                        
                        # Get gesture name
                        gesture_display, gesture = self.get_gesture_name(fingers)

                # Update gesture display labels
                self.current_gesture_label.configure(text=f"Current Gesture: {gesture_display}")
                self.finger_status_label.configure(text=f"Fingers: {finger_status}")

                # Trigger gesture only if cooldown passed or new
                current_time = time.time()
                if gesture and self.video_loaded and (gesture != self.last_gesture or current_time - self.last_time > self.gesture_cooldown):
                    fps = self.video.get(cv2.CAP_PROP_FPS)
                    pos = self.video.get(cv2.CAP_PROP_POS_FRAMES)

                    if gesture == "play":
                        self.playing = True
                        self.play_button.configure(text="Pause")
                    elif gesture == "pause":
                        self.playing = False
                        self.play_button.configure(text="Play")
                    elif gesture == "forward":
                        self.video.set(cv2.CAP_PROP_POS_FRAMES, pos + int(fps * 2))
                    elif gesture == "rewind":
                        self.video.set(cv2.CAP_PROP_POS_FRAMES, max(0, pos - int(fps * 2)))
                    elif gesture == "mute":
                        self.muted = not self.muted
                        self.mute_button.configure(text="Unmute" if self.muted else "Mute")
                    elif gesture == "restart":
                        self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        self.video.read()
                        self.playing = True

                    self.last_gesture = gesture
                    self.last_time = current_time

                # Update gesture window
                cam_frame = cv2.cvtColor(cam_frame, cv2.COLOR_BGR2RGB)
                cam_frame = cv2.resize(cam_frame, (320, 240))
                cam_photo = ImageTk.PhotoImage(Image.fromarray(cam_frame))
                self.gesture_canvas.create_image(0, 0, anchor="nw", image=cam_photo)
                self.gesture_canvas.image = cam_photo

                # Update video frame if playing
                if self.playing and self.video_loaded and self.video is not None:
                    ret_vid, frame = self.video.read()
                    if ret_vid:
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        
                        # Calculate aspect ratio
                        video_ratio = frame.shape[1] / frame.shape[0]
                        canvas_width = self.video_canvas.winfo_width()
                        canvas_height = self.video_canvas.winfo_height()
                        
                        if canvas_width > 1 and canvas_height > 1:
                            canvas_ratio = canvas_width / canvas_height

                            if video_ratio > canvas_ratio:
                                # Fit to width
                                new_width = canvas_width
                                new_height = int(canvas_width / video_ratio)
                            else:
                                # Fit to height
                                new_height = canvas_height
                                new_width = int(canvas_height * video_ratio)
                            
                            frame = cv2.resize(frame, (new_width, new_height))

                            # Apply volume/mute effect if needed
                            volume = 0 if self.muted else self.volume_slider.get() / 100
                            if volume < 0.1:  # Visual indicator for mute/low volume
                                frame = cv2.convertScaleAbs(frame, alpha=0.7)  # Dim the video

                            video_photo = ImageTk.PhotoImage(Image.fromarray(frame))
                            
                            # Center the video in canvas
                            x = (canvas_width - new_width) // 2
                            y = (canvas_height - new_height) // 2
                            self.video_canvas.create_image(x, y, anchor="nw", image=video_photo)
                            self.video_canvas.image = video_photo

                        # Update progress and time
                        total_frames = self.video.get(cv2.CAP_PROP_FRAME_COUNT)
                        current_frame = self.video.get(cv2.CAP_PROP_POS_FRAMES)
                        fps = self.video.get(cv2.CAP_PROP_FPS)
                        
                        if total_frames > 0:
                            # Update progress bar
                            progress = current_frame / total_frames
                            self.progress_bar.set(progress)
                            
                            # Update time display
                            current_time_sec = current_frame / fps if fps > 0 else 0
                            total_time = total_frames / fps if fps > 0 else 0
                            time_text = f"{self.format_time(current_time_sec)} / {self.format_time(total_time)}"
                            self.time_label.configure(text=time_text)
                    else:
                        # Video ended, restart
                        self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        self.playing = False
                        self.play_button.configure(text="Play")

                self.update()  # Update the tkinter window
                time.sleep(0.03)  # ~30 FPS
            except Exception as e:
                print(f"Error in update_frames: {e}")
                break

    def cleanup(self):
        self.running = False
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


