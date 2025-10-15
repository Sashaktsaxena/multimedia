import cv2
import mediapipe as mp
import time
import customtkinter as ctk
from PIL import Image, ImageTk
import threading
from tkinter import Canvas

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

        # Video canvas with 16:9 aspect ratio
        self.video_canvas = Canvas(self.video_frame, bg="black", width=960, height=540)
        self.video_canvas.pack(pady=10, padx=10, fill="both", expand=True)

        # Time display
        self.time_frame = ctk.CTkFrame(self.controls_frame)
        self.time_frame.pack(fill="x", padx=10, pady=(10, 5))
        
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

        self.play_button = ctk.CTkButton(self.left_controls, text="Play", width=80, command=self.toggle_play)
        self.play_button.pack(side="left", padx=5)

        self.mute_button = ctk.CTkButton(self.left_controls, text="Mute", width=80, command=self.toggle_mute)
        self.mute_button.pack(side="left", padx=5)

        # Right side volume control
        self.right_controls = ctk.CTkFrame(self.button_frame)
        self.right_controls.pack(side="right")

        self.volume_slider = ctk.CTkSlider(self.right_controls, from_=0, to=100, width=100)
        self.volume_slider.pack(side="right", padx=5)
        self.volume_slider.set(100)

        # Gesture view with 4:3 aspect ratio for better hand tracking
        self.gesture_canvas = Canvas(self.gesture_frame, width=320, height=240, bg="black")
        self.gesture_canvas.pack(pady=10, padx=10)

        # Load video
        self.video = cv2.VideoCapture('your_video.mp4')
        if not self.video.isOpened():
            print("❌ Cannot open video file.")
            exit()

        # Start webcam
        self.cam = cv2.VideoCapture(0)
        if not self.cam.isOpened():
            print("❌ Cannot access webcam.")
            exit()

        # Start video thread
        self.video_thread = threading.Thread(target=self.update_frames, daemon=True)
        self.video_thread.start()

        # State variables
        self.playing = True
        self.muted = False
        self.last_gesture = None
        self.last_time = time.time()
        self.gesture_cooldown = 1.5  # seconds

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
        if not self.video.isOpened():
            return
        # Calculate click position ratio
        click_x = event.x
        bar_width = self.progress_bar.winfo_width()
        ratio = click_x / bar_width
        
        # Set video position
        total_frames = self.video.get(cv2.CAP_PROP_FRAME_COUNT)
        target_frame = int(total_frames * ratio)
        self.video.set(cv2.CAP_PROP_POS_FRAMES, target_frame)

    def toggle_play(self):
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

    def update_frames(self):
        while True:
            # Read webcam
            ret_cam, cam_frame = self.cam.read()
            if not ret_cam:
                break
            cam_frame = cv2.flip(cam_frame, 1)
            cam_rgb = cv2.cvtColor(cam_frame, cv2.COLOR_BGR2RGB)
            results = hands.process(cam_rgb)

            # Detect gesture
            gesture = None
            if results.multi_hand_landmarks:
                for handLms in results.multi_hand_landmarks:
                    mp_draw.draw_landmarks(cam_frame, handLms, mp_hands.HAND_CONNECTIONS)
                    fingers = self.get_fingers_up(handLms)

                    if fingers == [0, 1, 1, 1, 1]:       gesture = "play"
                    elif fingers == [0, 0, 0, 0, 0]:     gesture = "pause"
                    elif fingers == [0, 1, 0, 0, 0]:     gesture = "forward"
                    elif fingers == [1, 0, 0, 0, 0]:     gesture = "rewind"
                    elif fingers == [0, 1, 1, 0, 0]:     gesture = "mute"
                    elif fingers == [0, 1, 0, 0, 1]:     gesture = "restart"

            # Trigger gesture only if cooldown passed or new
            current_time = time.time()
            if gesture and (gesture != self.last_gesture or current_time - self.last_time > self.gesture_cooldown):
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
            cam_photo = ImageTk.PhotoImage(Image.fromarray(cam_frame))
            self.gesture_canvas.create_image(0, 0, anchor="nw", image=cam_photo)
            self.gesture_canvas.image = cam_photo

            # Update video frame if playing
            if self.playing:
                ret_vid, frame = self.video.read()
                if ret_vid:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Calculate aspect ratio
                    video_ratio = frame.shape[1] / frame.shape[0]
                    canvas_width = self.video_canvas.winfo_width()
                    canvas_height = self.video_canvas.winfo_height()
                    canvas_ratio = canvas_width / canvas_height

                    if canvas_width > 0 and canvas_height > 0:
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
                    
                    # Update progress bar
                    progress = current_frame / total_frames
                    self.progress_bar.set(progress)
                    
                    # Update time display
                    current_time = current_frame / fps
                    total_time = total_frames / fps
                    time_text = f"{self.format_time(current_time)} / {self.format_time(total_time)}"
                    self.time_label.configure(text=time_text)
                else:
                    # Video ended, restart
                    self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)

            self.update()  # Update the tkinter window
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def cleanup(self):
        self.cam.release()
        self.video.release()
        cv2.destroyAllWindows()
        self.quit()

if __name__ == "__main__":
    app = MediaPlayer()
    app.protocol("WM_DELETE_WINDOW", app.cleanup)
    app.mainloop()


