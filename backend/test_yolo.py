"""
YOLOv8 ALPR Inference Tester
Use this script to test your newly trained YOLO model on images or videos
before we integrate it live into the mock ALPR camera event dispatcher.

INSTALLATION:
    pip install ultralytics opencv-python

USAGE:
    1. Place your `best.pt` file inside the `backend/models/` folder.
    2. Change `SOURCE` below to an image or video path.
    3. Run: python test_yolo.py
"""

import os
from ultralytics import YOLO
import cv2
import easyocr
import re
import collections
import time

# ── Configuration ──
# Create a 'models' folder in the backend and place your best.pt there
MODEL_PATH = "models/best.pt" 

# Change this to a test image (.jpg) or test video (.mp4) from your dataset
SOURCE = "models/test2.mp4" 

def format_indian_plate(text):
    """
    Applies heuristics to fix common OCR mistakes based on the Indian license plate format.
    Standard (10 chars): XX 00 XX 0000 (State, RTO, Series, Number)
    Shorter (9 chars): XX 00 X 0000
    """
    clean_text = re.sub(r'[^A-Z0-9]', '', text.upper())
    
    # Typical OCR confusion mappings
    d_c2i = {'O': '0', 'I': '1', 'J': '3', 'A': '4', 'G': '6', 'S': '5', 'B': '8', 'Z': '2', 'E': '6', 'T': '7', 'Q': '0', 'D': '0'}
    d_i2c = {'0': 'O', '1': 'I', '3': 'J', '4': 'A', '6': 'G', '5': 'S', '8': 'B', '2': 'Z', '7': 'T'}
    
    formatted = ""
    for idx, c in enumerate(clean_text):
        if len(clean_text) == 10:
            if idx in [0, 1] or idx in [4, 5]:  # Must be Letters
                formatted += d_i2c.get(c, c) if c.isdigit() else c
            elif idx in [2, 3] or idx in [6, 7, 8, 9]:  # Must be Numbers
                formatted += d_c2i.get(c, c) if c.isalpha() else c
        elif len(clean_text) == 9:
            if idx in [0, 1] or idx == 4:  # Must be Letters
                formatted += d_i2c.get(c, c) if c.isdigit() else c
            elif idx in [2, 3] or idx in [5, 6, 7, 8]:  # Must be Numbers
                formatted += d_c2i.get(c, c) if c.isalpha() else c
        else:
            return clean_text # Unrecognized length, just return alphanumeric
            
    return formatted

def test_inference():
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Model not found at '{MODEL_PATH}'")
        print("\nPlease create a folder named 'models' inside the 'backend' folder")
        print("and copy your trained 'best.pt' file into it.")
        return

    print(f"✅ Loading custom YOLO model from {MODEL_PATH}...")
    model = YOLO(MODEL_PATH)
    
    print("✅ Loading EasyOCR English reader (this might take a few seconds)...")
    reader = easyocr.Reader(['en'], gpu=True) # Set gpu=False if you don't have an NVIDIA GPU setup

    if not os.path.exists(SOURCE) and SOURCE != "0": # 0 is for webcam
         print(f"⚠️ Video source '{SOURCE}' not found in the backend folder.")
         print("Please update the SOURCE variable in this script to point to a valid image/video file.")
         return

    print(f"\n🚀 Starting live video inference + OCR on {SOURCE}...")
    print("Press 'q' on your keyboard to stop the video.")
    
    cap = cv2.VideoCapture(SOURCE)
    
    # ── ALPR Consensus Voting & Debounce Engine ──
    plate_buffer = []  # Stores OCR reads for the current vehicle
    cooldowns = {}     # Stores {plate_text: last_seen_time} to prevent duplicate entries
    frames_without_plate = 0
    
    # Loop through the video frames
    while cap.isOpened():
        success, frame = cap.read()
        
        if success:
            # Run YOLO prediction on the current frame
            # stream=True is much faster for continuous video
            results = model.predict(frame, stream=True, conf=0.5, verbose=False)
            
            # The results object contains the annotated frame with bounding boxes
            boxes_found = False
            for r in results:
                annotated_frame = frame.copy()
                boxes = r.boxes
                
                if len(boxes) > 0:
                    boxes_found = True
                    frames_without_plate = 0
                
                for box in boxes:
                    # Bounding box coordinates
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = box.conf[0].item()
                    
                    # 1. Crop the plate from the original frame
                    plate_crop = frame[y1:y2, x1:x2]
                    
                    if plate_crop.size > 0:
                        # 2. Basic Preprocessing for better OCR
                        gray_crop = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
                        # Optional: resize to make text larger for the reader
                        gray_crop = cv2.resize(gray_crop, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

                        # 3. Read Text with EasyOCR
                        ocr_results = reader.readtext(gray_crop, detail=0) # detail=0 returns just strings
                        
                        # 4. Clean text (Alphanumeric only for Indian plates)
                        if ocr_results:
                            raw_text = "".join(ocr_results)
                            clean_text = format_indian_plate(raw_text)
                            # Add to consensus buffer if it's a valid plate length
                            if len(clean_text) >= 8:
                                plate_buffer.append(clean_text)
                        else:
                            clean_text = "UNKNOWN"
                            
                        # 5. Draw bounding box and the OCR text on the live video frame
                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        
                        label = f"{clean_text} ({conf:.2f})"
                        # Draw label background
                        cv2.rectangle(annotated_frame, (x1, y1 - 30), (x1 + len(label) * 15, y1), (0, 255, 0), -1)
                        # Draw text
                        cv2.putText(annotated_frame, label, (x1 + 5, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
                        
                        print(f"📷 YOLO Conf: {conf:.2f} | 🔤 EasyOCR Read: {clean_text}")

            # ── 6. Consensus Voting Logic ──
            # If the vehicle has left the frame (no boxes for ~10 frames)
            if not boxes_found:
                frames_without_plate += 1
                
            if frames_without_plate > 10 and len(plate_buffer) > 0:
                # Find the most frequent OCR read (mode)
                counter = collections.Counter(plate_buffer)
                best_plate, count = counter.most_common(1)[0]
                confidence_ratio = count / len(plate_buffer)
                
                # Debounce / Cooldown Check (ignore same plate for 30s)
                current_time = time.time()
                if best_plate not in cooldowns or (current_time - cooldowns[best_plate] > 30):
                    print("\n" + "="*60)
                    print(f"🎉 FINAL CONFIRMED PLATE: {best_plate}")
                    print(f"📊 Consensus: {count}/{len(plate_buffer)} frames ({confidence_ratio:.0%})")
                    print(f"🚀 >> Sending real {best_plate} entry to Firebase... <<")
                    print("="*60 + "\n")
                    
                    cooldowns[best_plate] = current_time
                
                # Clear buffer for the next car
                plate_buffer.clear()

            # Resize the window if the video is too large (like 4k)
            # annotated_frame = cv2.resize(annotated_frame, (1280, 720))
                
            # Display the annotated frame
            cv2.imshow("YOLOv8 + EasyOCR - Live Test", annotated_frame)
            
            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        else:
            # End of video
            break

    # Release the video capture object and close windows
    cap.release()
    cv2.destroyAllWindows()
    print("\n✅ Inference complete!")

if __name__ == "__main__":
    test_inference()
