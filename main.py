# main.py
import ctypes
import sys
sys.stdout.reconfigure(encoding='utf-8')
import time
import keyboard
from config import *
from window_util import *
from color_util import *
from utils import save_screenshot
from game_logic import check_and_replace_rod

def detect_continue_button(full_img, width, height):
    """
    Detect the continue fishing button using white text detection in the bottom-right area
    """
    # Define the area where the continue button appears (bottom-right quadrant)
    button_area = get_scale_area((width//2, height//2, width, height), width, height)
    bx1, by1, bx2, by2 = button_area
    
    if (bx1 >= 0 and by1 >= 0 and bx2 <= full_img.shape[1] and by2 <= full_img.shape[0]):
        button_region = full_img[by1:by2, bx1:bx2]
        
        if button_region.size > 0:
            # Convert to grayscale and threshold for white text
            gray = cv2.cvtColor(button_region, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
            
            # Count white pixels (potential text)
            white_pixels = cv2.countNonZero(thresh)
            total_pixels = gray.shape[0] * gray.shape[1]
            white_ratio = white_pixels / total_pixels
            
            # Look for clusters of white pixels (text)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            text_areas = [cv2.contourArea(cnt) for cnt in contours if cv2.contourArea(cnt) > 50]
            
            # If we have significant white text areas, likely the button is there
            if white_ratio > 0.02 and len(text_areas) > 0:
                return True
    
    return False

def get_continue_button_position(width, height):
    """
    Return position to click for continue button (bottom-right area)
    """
    # Position for the continue button in bottom-right
    continue_x = width - 200  # 200 pixels from right edge
    continue_y = height - 100  # 100 pixels from bottom edge
    return continue_x, continue_y

def monitor_window(hwnd):
    isRunning = [True]
    last_key = [None]  # Record last long-pressed "a" or "d"
    window = get_window_by_hwnd(hwnd)
    if not window:
        log(f"Window corresponding to handle {hwnd} not found")
        return

    def on_esc_press(e):
        if e.event_type == keyboard.KEY_DOWN and e.name.lower() in ('esc', '~', 'q', 'ctrl'):
            log(f"Detected {e.name} key press, program will exit soon...")
            isRunning[0] = False

    keyboard.on_press(on_esc_press)
    log("Program started, press Esc key to exit at any time")
    window.activate()
    log("Switched to target window")
    time.sleep(1)

    try:
        while isRunning[0]:
            full_img = capture_window(hwnd)
            if full_img is None:
                log("Failed to capture window, retrying...")
                time.sleep(1)
                continue
                
            height, width = full_img.shape[:2]
            
            # Check rod durability
            rod_replaced = check_and_replace_rod(full_img, width, height, hwnd, window)
            if rod_replaced:
                log("Rod replaced, continuing fishing...")
                time.sleep(2)
                continue
                
            click_mouse_window(hwnd, *get_scale_point(CLICK_POS, width, height))
            log(f"Casting hook, detecting red dot after {START_DELAY} seconds")

            # Initial delay
            time.sleep(2.5)
            full_img = capture_window(hwnd)

            # Check for fish escape during delay
            time.sleep(1)
            delay_start = time.time()
            blue_detected = False
            while time.time() - delay_start < (START_DELAY - 2):
                full_img = capture_window(hwnd)
                if full_img is not None:
                    if is_blue_target(full_img, get_scale_area(BLUE_ROI,width,height), BLUE_COLORS, tolerance=BLUE_TOLERANCE):
                        log("Fish escaped")
                        blue_detected = True
                        break
                time.sleep(0.05)
            if blue_detected:
                continue

            # ====== Step 2: Automatically locate dense red dot region ======
            full_img = capture_window(hwnd)
            found_red = False
            count = 0
            fish_region = []
            red_rect = None
            red_ratio = 0
            
            while not found_red and count<3:
                offset = count * 100  # Offset 100 pixels each time
                center = (RED_SEARCH_REGION_CENTER[0], RED_SEARCH_REGION_CENTER[1] + offset)
                red_rect, red_ratio = find_max_red_region(
                    full_img, get_search_region(get_scale_point(center,width,height), RED_SEARCH_REGION_OFFSET), RED_DETECT_BOX_SIZE, RED_THRESHOLD)
                log(f"Detected red dot region: {red_rect}, density={red_ratio:.2f}")
                fish_region = red_rect
                count+=1
                if red_ratio >= RED_THRESHOLD:
                    found_red = True
                    break
                    
            if red_ratio < RED_THRESHOLD:
                log("Red dot not found")
                continue

            red_start_time = None
            is_pressed = False
            cycle_active = True
            blue_check_enable = True
            minigame_start_time = None
            last_continue_check = 0

            log("👀 Watching bobber for bite...")
            
            while cycle_active and isRunning[0]:
                full_img = capture_window(hwnd)
                if full_img is None:
                    time.sleep(0.1)
                    continue

                if blue_check_enable and is_blue_target(full_img, get_scale_area(BLUE_ROI,width,height), BLUE_COLORS, tolerance=BLUE_TOLERANCE):
                    log("Fish escaped")
                    if is_pressed:
                        release_mouse()
                    break

                # Only monitor the red dot region automatically detected this round
                x1, y1, x2, y2 = red_rect
                
                if not is_pressed: 
                    roi = full_img[y1:y2, x1:x2]
                    red = is_red_dominant(roi, threshold=RED_THRESHOLD)
                    white = is_white_dominant(roi, threshold=0.2)

                # KEY: Red gone + White splash = Fish bit!
                if not red and white:
                    if not is_pressed:
                        # Use scaled coordinates for mouse press
                        press_mouse_window(hwnd, *get_scale_point(CLICK_POS, width, height))
                        is_pressed = True
                        minigame_start_time = time.time()
                        last_continue_check = time.time()
                        log("🎣 Fish bit! Starting minigame (60s timeout)...")
                else:
                    red_start_time = None

                # ------- A/D mutually exclusive long-press logic -------
                if is_pressed:
                    # 60 SECOND TIMEOUT: Minigame can last up to 60 seconds
                    if minigame_start_time and time.time() - minigame_start_time > 60:
                        log("⏱️ Minigame timeout (60s) - Releasing mouse")
                        release_mouse()
                        if last_key[0] == "a":
                            keyboard.release("a")
                        if last_key[0] == "d":
                            keyboard.release("d")
                        last_key[0] = None
                        cycle_active = False
                        break
                    
                    # Check for continue button every 2 seconds during minigame
                    current_time = time.time()
                    if current_time - last_continue_check >= 2.0:
                        last_continue_check = current_time
                        if detect_continue_button(full_img, width, height):
                            log("📋 Continue button detected during minigame - fish caught!")
                            release_mouse()
                            is_pressed = False
                            blue_check_enable = False
                            
                            # Click continue button
                            continue_x, continue_y = get_continue_button_position(width, height)
                            click_mouse_window(hwnd, continue_x, continue_y)
                            
                            log(f"Waiting {AFTER_SECOND_CLICK_DELAY} seconds before next cast")
                            time.sleep(AFTER_SECOND_CLICK_DELAY)
                            cycle_active = False
                            if last_key[0] == "a":
                                keyboard.release("a")
                            if last_key[0] == "d":
                                keyboard.release("d")
                            last_key[0] = None
                            break
                    
                    best_rect, best_score = find_best_water_region(full_img,fish_region,"assets/water_left.png")
                    target_key = None
                    if best_score < 0.001:
                        center_x = -1
                        target_key = last_key[0]
                    else:
                        center_x = best_rect[0] + best_rect[2] / 2
                        if abs(center_x - width / 2) <= 200:
                            target_key = None
                        elif center_x<width/2:
                            target_key = "a"
                        else:
                            target_key = "d"
                    if target_key != last_key[0]:
                        if last_key[0] == "a":
                            keyboard.release("a")
                        elif last_key[0] == "d":
                            keyboard.release("d")
                        last_key[0] = target_key
                    if target_key:
                        keyboard.press(target_key)
                    if best_score and center_x:
                        log(f"target_key = {target_key or 'None'}, best_score = {best_score:.4f}, center_x = {center_x:.2f}")
                    
                    # Check for fishing completion (gray area)
                    cx1, cy1, cx2, cy2 = get_scale_area(COLOR_CHECK_AREA,width, height)
                    if is_color_match(full_img, cx1, cy1, cx2, cy2, TARGET_COLOR):
                        log(f"✅ Fishing completed - Gray area detected!")
                        release_mouse()
                        is_pressed = False
                        blue_check_enable = False
                        
                        # Wait for continue screen
                        time.sleep(2)
                        
                        # Check for continue button
                        continue_detected = False
                        for i in range(5):  # Check for 5 seconds
                            full_img = capture_window(hwnd)
                            if full_img is not None:
                                if detect_continue_button(full_img, width, height):
                                    log("📋 Continue button detected, clicking...")
                                    continue_x, continue_y = get_continue_button_position(width, height)
                                    click_mouse_window(hwnd, continue_x, continue_y)
                                    continue_detected = True
                                    break
                            time.sleep(1)
                        
                        if not continue_detected:
                            log("No continue button, using normal flow")
                            time.sleep(AFTER_DETECT_CLICK_DELAY)
                            click_mouse_window(hwnd, *(get_scale_point(SECOND_CLICK_POS,width,height)))
                        
                        log(f"Waiting {AFTER_SECOND_CLICK_DELAY} seconds before next cast")
                        time.sleep(AFTER_SECOND_CLICK_DELAY)
                        cycle_active = False
                        if last_key[0] == "a":
                            keyboard.release("a")
                        if last_key[0] == "d":
                            keyboard.release("d")
                        last_key[0] = None
                else:
                    if last_key[0] == "a":
                        keyboard.release("a")
                        last_key[0] = None
                    if last_key[0] == "d":
                        keyboard.release("d")
                        last_key[0] = None

                time.sleep(0.04)
    except Exception as e:
        log("Exception occurred:", e)
        import traceback
        traceback.print_exc()
    finally:
        release_mouse()
        if last_key[0] == "a":
            keyboard.release("a")
        if last_key[0] == "d":
            keyboard.release("d")
        keyboard.unhook_all()
        log("Program terminated.")

if __name__ == "__main__":
    hwnds = find_window_by_process_name(PROCESS_NAME)
    if not hwnds:
        log(f"Window named {PROCESS_NAME} not found")
    else:
        hwnd = hwnds[0]
        log("Started monitoring window:", win32gui.GetWindowText(hwnd))
        monitor_window(hwnd)