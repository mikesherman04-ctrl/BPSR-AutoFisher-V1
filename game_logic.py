# game_logic.py
import time
import keyboard
import cv2
import numpy as np
from window_util import *
from color_util import *
from config import *

def match_rod_template(full_img, template_path, roi_scale=(0.75, 0.75), match_method=cv2.TM_CCOEFF_NORMED):
    """
    Match template image in the bottom-right region of full_img, return best_score and location.
    """
    try:
        # Load and convert template to grayscale
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            raise FileNotFoundError(f"Template file not found: {template_path}")
        
        # Convert to grayscale
        full_gray = cv2.cvtColor(full_img, cv2.COLOR_BGR2GRAY)
        h, w = full_gray.shape

        # Define bottom-right search area (proportional crop)
        roi_x = int(w * (1 - roi_scale[0]))
        roi_y = int(h * (1 - roi_scale[1]))
        roi = full_gray[roi_y:h, roi_x:w]

        # Perform matching
        res = cv2.matchTemplate(roi, template, match_method)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        best_score = max_val if match_method in [cv2.TM_CCOEFF_NORMED, cv2.TM_CCORR_NORMED] else -min_val

        return best_score, max_loc, template.shape
    except Exception as e:
        log(f"Error in match_rod_template: {e}")
        return 0, (0, 0), (0, 0)

def check_and_replace_rod(full_img, width, height, hwnd, window):
    """
    Check if fishing rod has no durability, if so execute rod replacement process.
    """
    try:
        # First check if we have a good rod (high confidence)
        good_rod_score, _, _ = match_rod_template(full_img, "assets/good_rod.png")
        
        # Then check if we need to add a rod
        need_change_rod_score, _, _ = match_rod_template(full_img, "assets/add_rod.png")
        
        log(f"Rod check - Good rod: {good_rod_score:.3f}, Add rod: {need_change_rod_score:.3f}")
        
        # Calculate the difference
        score_difference = good_rod_score - need_change_rod_score
        
        # CLEAR THRESHOLDS BASED ON TEST DATA:
        # Good rod: good_rod > 0.9 and difference > 0.1
        # Broken rod: add_rod > 0.85 and difference < -0.1
        
        # If good rod is clearly better, don't replace
        if good_rod_score > 0.9 and score_difference > 0.1:
            log("✅ Good rod detected (clear difference), no replacement needed")
            return False
            
        # If add rod is clearly better, replace
        if need_change_rod_score > 0.85 and score_difference < -0.1:
            log("🔧 Fishing rod has no durability, replacing rod")

            # Step 1: Simulate key press
            keyboard.press(ROD_NO_DURABILITY_KEY)
            time.sleep(0.05)
            keyboard.release(ROD_NO_DURABILITY_KEY)
            time.sleep(ROD_NO_DURABILITY_DELAY)

            # Step 2: Click replacement position
            window.activate()
            click_mouse_window(hwnd, *get_scale_point(ROD_CHANGE_CLICK_POS, width, height))
            time.sleep(ROD_NO_DURABILITY_DELAY)

            return True
        
        # If we're uncertain, assume rod is good (to avoid false replacements)
        log(f"❓ Uncertain rod state - Good: {good_rod_score:.3f}, Add: {need_change_rod_score:.3f}, Diff: {score_difference:.3f}")
        return False
    except Exception as e:
        log(f"Error in check_and_replace_rod: {e}")
        return False