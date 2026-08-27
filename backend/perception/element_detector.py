import cv2
import numpy as np
from typing import List, Dict, Any

class ElementDetector:
    def __init__(self):
        pass

    def detect_elements(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Processes image bytes using OpenCV to find visual elements like inputs and buttons.
        """
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return []

        h, w, _ = img.shape
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian Blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Adaptive thresholding to handle light/dark mode webpages
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detected = []
        for i, cnt in enumerate(contours):
            x, y, rect_w, rect_h = cv2.boundingRect(cnt)
            
            # Filter contours by size to match buttons, text inputs, checkboxes
            # We filter out extremely small elements (like noise) and extremely large elements (like container divs)
            if rect_w < 8 or rect_h < 8:
                continue
            if rect_w > w * 0.9 or rect_h > h * 0.9:
                continue
                
            # Classify elements based on aspect ratio and size
            aspect_ratio = rect_w / float(rect_h)
            area = rect_w * rect_h
            
            element_type = "ELEMENT"
            confidence = 0.70
            
            # Heuristic classifications:
            # 1. Checkboxes/Radio buttons are small squares
            if 8 <= rect_w <= 30 and 8 <= rect_h <= 30 and 0.8 <= aspect_ratio <= 1.25:
                element_type = "CHECKBOX"
                confidence = 0.85
            # 2. Input fields are horizontal rectangles of moderate height
            elif 80 <= rect_w <= 600 and 20 <= rect_h <= 60:
                element_type = "INPUT"
                confidence = 0.88
            # 3. Buttons are slightly wider or rounded rectangles
            elif 50 <= rect_w <= 300 and 25 <= rect_h <= 70:
                element_type = "BUTTON"
                confidence = 0.82
            
            # Add to detected list
            detected.append({
                "id": f"vis_{i}",
                "type": element_type,
                "bbox": [x, y, x + rect_w, y + rect_h],
                "confidence": confidence,
                "source": "VISION"
            })
            
        return detected
