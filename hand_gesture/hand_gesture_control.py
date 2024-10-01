import cv2
import mediapipe as mp
import pyautogui
import os
import math

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_drawing = mp.solutions.drawing_utils

# Get screen size for cursor movement
screen_width, screen_height = pyautogui.size()

# Open video capture window (0 is for default webcam)
cap = cv2.VideoCapture(0)

# Track the state of gestures
gesture_active = False  # Only one gesture should work at a time

# For controlling system volume (you may need to implement OS-specific volume control)
volume_level = 50  # Initial volume (as a placeholder)
max_volume = 100
min_volume = 0

# Variables to store previous cursor position for smoothing
prev_cursor_x, prev_cursor_y = None, None
smooth_factor = 0.2  # Adjust smoothing factor (0 < smooth_factor < 1)

def calculate_distance(point1, point2):
    return math.sqrt((point1.x - point2.x) ** 2 + (point1.y - point2.y) ** 2)

def set_volume(direction):
    global volume_level
    if direction == "up" and volume_level < max_volume:
        volume_level += 2  # Increase volume
        print(f"Volume Up: {volume_level}%")
        # Add OS-specific volume control here
    elif direction == "down" and volume_level > min_volume:
        volume_level -= 2  # Decrease volume
        print(f"Volume Down: {volume_level}%")
        # Add OS-specific volume control here

def zoom_in_out(thumb_index_distance):
    if thumb_index_distance < 0.3:  # Zoom in
        pyautogui.hotkey('ctrl', '+')
        print("Zoom In")
    elif thumb_index_distance > 0.3:  # Zoom out
        pyautogui.hotkey('ctrl', '-')
        print("Zoom Out")

while True:
    # Read a frame from the webcam
    _, frame = cap.read()
    frame = cv2.flip(frame, 1)  # Flip frame horizontally for natural interaction
    height, width, _ = frame.shape

    # Convert the frame to RGB (MediaPipe works with RGB images)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Get hand landmarks from MediaPipe
    result = hands.process(rgb_frame)

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            # Draw the hand landmarks on the frame
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Get the index finger tip (landmark 8), middle finger tip (landmark 12), and thumb tip (landmark 4)
            index_finger_tip = hand_landmarks.landmark[8]
            middle_finger_tip = hand_landmarks.landmark[12]
            thumb_tip = hand_landmarks.landmark[4]

            # Calculate the cursor position based on the index finger tip
            cursor_x = int(index_finger_tip.x * screen_width)
            cursor_y = int(index_finger_tip.y * screen_height)

            # Smooth the cursor movement
            if prev_cursor_x is not None and prev_cursor_y is not None:
                # Apply smoothing: blend the current position with the previous position
                cursor_x = int(prev_cursor_x * (1 - smooth_factor) + cursor_x * smooth_factor)
                cursor_y = int(prev_cursor_y * (1 - smooth_factor) + cursor_y * smooth_factor)

            # Move the cursor based on the smoothed hand movement
            pyautogui.moveTo(cursor_x, cursor_y)

            # Store the current position as previous position for next frame
            prev_cursor_x, prev_cursor_y = cursor_x, cursor_y

            # Calculate distance between thumb and index finger for zoom gestures
            thumb_index_distance = calculate_distance(thumb_tip, index_finger_tip)

            # Gesture for volume control (index finger moving up/down)
            if not gesture_active and abs(index_finger_tip.y - thumb_tip.y) > 0.2:
                gesture_active = True
                if index_finger_tip.y < thumb_tip.y:
                    set_volume("up")
                else:
                    set_volume("down")
                gesture_active = False  # Reset after volume adjustment

            # Gesture for zooming (thumb and index finger distance)
            elif not gesture_active and 0.1 < thumb_index_distance < 0.7:
                gesture_active = True
                zoom_in_out(thumb_index_distance)
                gesture_active = False

            # Gesture for right-click (index finger forward)
            elif not gesture_active and index_finger_tip.y < middle_finger_tip.y:
                gesture_active = True
                pyautogui.rightClick()
                print("Right Click")
                gesture_active = False

            # Gesture for left-click (middle finger forward)
            elif not gesture_active and middle_finger_tip.y < index_finger_tip.y:
                gesture_active = True
                pyautogui.click()
                print("Left Click")
                gesture_active = False

    # Show the video frame
    cv2.imshow("Hand Gesture Control", frame)

    # Break the loop with 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the webcam and close windows
cap.release()
cv2.destroyAllWindows()
