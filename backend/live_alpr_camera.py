"""
LIVE ALPR CAMERA SENSOR
Run this script to open the webcam or video file.
It uses YOLO and EasyOCR to scan license plates,
builds consensus, and pushes real EVENT triggers to Firebase in the background.

Usage:
    python live_alpr_camera.py
"""

import os
import cv2
import easyocr
import re
import collections
import time
import uuid
import threading

from ultralytics import YOLO
from firebase_config import ref
from cloudinary_service import upload_gate_image_from_bytes

# ── Configuration ──
MODEL_PATH = "models/best.pt" 
# Change to "0" for live webcam, or video path like "models/test2.mp4"
SOURCE = "models/test2 (1).mp4" 

# Base identification for this camera node
GATE_ID = "gate_2"


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


def push_event(plate: str, confidence: float, image_url: str, gate_type: str):
    """Push a REAL ALPR event to Firebase for the Cloud Brain to process."""
    event_id = str(uuid.uuid4())
    event_data = {
        "plate_number": plate,
        "gate_type": gate_type,
        "confidence": confidence,
        "timestamp": int(time.time() * 1000),
        "resolved_status": "PENDING",
        "gate_id": GATE_ID,
        "image_url": image_url,
    }
    
    # Run the network request in a daemon thread so it DOES NOT freeze the live video feed!
    def _upload():
        try:
            ref(f"/gate_events/{event_id}").set(event_data)
            ts = time.strftime("%H:%M:%S")
            print(f"  ☁️  [{ts}] Firebase Upload Success: {plate} -> {gate_type} @ {GATE_ID}")
        except Exception as e:
            print(f"  ❌ Failed to push event to Firebase: {e}")
            
    threading.Thread(target=_upload, daemon=True).start()


def run_live_camera():
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Model not found at '{MODEL_PATH}'")
        return

    print(f"✅ Loading ALPR custom YOLO model...")
    model = YOLO(MODEL_PATH)
    
    print("✅ Loading EasyOCR English reader...")
    reader = easyocr.Reader(['en'], gpu=True) 

    if not os.path.exists(SOURCE) and SOURCE != "0": 
         print(f"⚠️ Video source '{SOURCE}' not found.")
         return

    print(f"\n🎥 🟢 LIVE CAMERA ACTIVATED: {SOURCE}")
    print(f"📡 Hardware ID: {GATE_ID}")
    print("\n⌨️  Keyboard Controls:")
    print("  [4] or [x] : Toggle Gate Mode (ENTRY <-> EXIT)")
    print("  [q]        : Stop Camera Simulator")
    
    cap = cv2.VideoCapture(SOURCE)
    
    # Toggleable Camera State
    current_gate_type = "entry"
    
    # ── ALPR Consensus Voting & Debounce Engine ──
    plate_buffer = [] 
    cooldowns = {}    
    frames_without_plate = 0
    
    while cap.isOpened():
        success, frame = cap.read()
        
        if success:
            results = model.predict(frame, stream=True, conf=0.5, verbose=False)
            
            boxes_found = False
            for r in results:
                annotated_frame = frame.copy()
                boxes = r.boxes
                
                if len(boxes) > 0:
                    boxes_found = True
                    frames_without_plate = 0
                
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = box.conf[0].item()
                    
                    plate_crop = frame[y1:y2, x1:x2]
                    
                    if plate_crop.size > 0:
                        gray_crop = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
                        gray_crop = cv2.resize(gray_crop, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

                        ocr_results = reader.readtext(gray_crop, detail=0) 
                        
                        if ocr_results:
                            raw_text = "".join(ocr_results)
                            clean_text = format_indian_plate(raw_text)
                            if len(clean_text) >= 8:
                                plate_buffer.append(clean_text)
                        else:
                            clean_text = "UNKNOWN"
                            
                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        
                        label = f"{clean_text} ({conf:.2f})"
                        cv2.rectangle(annotated_frame, (x1, y1 - 30), (x1 + len(label) * 15, y1), (0, 255, 0), -1)
                        cv2.putText(annotated_frame, label, (x1 + 5, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
                        
            # ── Draw Camera Status HUD ──
            status_color = (0, 255, 0) if current_gate_type == "entry" else (0, 0, 255)
            status_text = f"MODE: {current_gate_type.upper()}"
            cv2.putText(annotated_frame, status_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 3)
            cv2.putText(annotated_frame, "Press '4' to switch mode", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            # ── Consensus Voting Logic ──
            if not boxes_found:
                frames_without_plate += 1
                
            if frames_without_plate > 10 and len(plate_buffer) > 0:
                counter = collections.Counter(plate_buffer)
                best_plate, count = counter.most_common(1)[0]
                confidence_ratio = count / len(plate_buffer)
                
                current_time = time.time()
                # Ignore same plate for 45 seconds to prevent spam
                if best_plate not in cooldowns or (current_time - cooldowns[best_plate] > 45):
                    print("\n" + "="*60)
                    print(f"🎉 CONFIRMED VEHICLE AT GATE: {best_plate}")
                    print(f"📊 Accuracy Consensus: {count}/{len(plate_buffer)} frames ({confidence_ratio:.0%})")
                    print("☁️ Uploading frame snapshot to Cloudinary...")
                    print("="*60 + "\n")
                    
                    # 🔥 Encode the current video frame to JPEG bytes
                    _, buffer = cv2.imencode('.jpg', annotated_frame)
                    image_bytes = buffer.tobytes()
                    
                    # Upload Image & Push to Firebase in a background thread to prevent video lag!
                    def _upload_and_push(plate, conf, img_bytes, gt):
                        try:
                            # 1. Upload to Cloudinary
                            real_image_url = upload_gate_image_from_bytes(img_bytes, plate, GATE_ID)
                            print(f"  📸 Snapshot Cloud URL: {real_image_url}")
                            
                            # 2. Push the full event + Photo to Firebase
                            push_event(plate, conf, real_image_url, gt)
                        except Exception as e:
                            print(f"  ❌ Error uploading snapshot or pushing event: {e}")
                    
                    threading.Thread(target=_upload_and_push, args=(best_plate, float(confidence_ratio), image_bytes, current_gate_type), daemon=True).start()
                    
                    cooldowns[best_plate] = current_time
                
                plate_buffer.clear()
                
            # Resize the OpenCV window so it fits on standard monitors
            display_frame = cv2.resize(annotated_frame, (1280, 720))
            cv2.imshow(f"SCET ALPR Live Sensor | {GATE_ID}", display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("4") or key == ord("x"):
                current_gate_type = "exit" if current_gate_type == "entry" else "entry"
                print(f"\n🔄 Camera Mode Switched to: {current_gate_type.upper()}")
                
        else:
            break

    cap.release()
    cv2.destroyAllWindows()
    print("\n✅ Camera Offline.")

if __name__ == "__main__":
    run_live_camera()
