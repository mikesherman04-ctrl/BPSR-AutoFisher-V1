# window_util.py

from datetime import datetime
import win32gui
import win32process
import pygetwindow as gw
import ctypes
import cv2
import numpy as np
import mss

from config import *

def find_window_by_process_name(process_name):
    hwnds = []
    def enum_window_callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                import psutil
                proc = psutil.Process(pid)
                if proc.name().lower() == process_name.lower():
                    hwnds.append(hwnd)
            except Exception:
                pass
    win32gui.EnumWindows(enum_window_callback, None)
    return hwnds

def get_window_rect(hwnd):
    return win32gui.GetWindowRect(hwnd)

def get_client_rect(hwnd):
    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    # Convert to screen coordinates (absolute screen coordinates of client area top-left and bottom-right)
    left_top = win32gui.ClientToScreen(hwnd, (left, top))
    right_bottom = win32gui.ClientToScreen(hwnd, (right, bottom))
    return (left_top[0], left_top[1], right_bottom[0], right_bottom[1])

def capture_window(hwnd):
    try:
        # Capture only client area, excluding borders and title bar
        x1, y1, x2, y2 = get_client_rect(hwnd)
        width = x2 - x1
        height = y2 - y1
        with mss.mss() as sct:
            monitor = {"left": x1, "top": y1, "width": width, "height": height}
            sct_img = sct.grab(monitor)
            img = np.array(sct_img)# [:, :, :3]  # Remove alpha channel
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img
        # return img
        # log(f'client: width = {width},height = {height}')
        # screenshot = pyautogui.screenshot(region=(x1, y1, width, height))
        # log(f"Captured window client area screenshot: {x1},{y1} - {x2},{y2} (width: {width}, height: {height})")
        # img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        # utils.save_screenshot(img, f'save_screen shot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
        return img
    except Exception as e:
        log(f"Screenshot failed: {e}")
        return None

def press_mouse_window(hwnd, rel_x, rel_y):
    # Relative coordinates based on top-left corner of client area
    client_rect = get_client_rect(hwnd)
    abs_x = client_rect[0] + rel_x
    abs_y = client_rect[1] + rel_y
    ctypes.windll.user32.SetCursorPos(abs_x, abs_y)
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    log(f"Mouse left button pressed (in-window: {rel_x},{rel_y} | screen: {abs_x},{abs_y})")

def release_mouse():
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    log("Mouse left button released")

def click_mouse_window(hwnd, rel_x, rel_y):
    # Relative coordinates based on top-left corner of client area
    client_rect = get_client_rect(hwnd)
    abs_x = client_rect[0] + rel_x
    abs_y = client_rect[1] + rel_y
    ctypes.windll.user32.SetCursorPos(abs_x, abs_y)
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    import time
    time.sleep(0.01)
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    log(f"Mouse left click completed (in-window: {rel_x},{rel_y} | screen: {abs_x},{abs_y})")

def detect_continue_fishing_button(img, width, height):
    """
    Detect the 'Continue fishing' button using multiple methods
    """
    # Method 1: Look for white text in the button area
    button_roi = get_scale_area((1000, 650, 1400, 750), width, height)  # Wider area around the button
    bx1, by1, bx2, by2 = button_roi
    
    if (bx1 >= 0 and by1 >= 0 and bx2 <= img.shape[1] and by2 <= img.shape[0]):
        button_region = img[by1:by2, bx1:bx2]
        
        if button_region.size > 0:
            # Convert to grayscale and threshold for white text
            gray = cv2.cvtColor(button_region, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
            
            # Count white pixels (potential text)
            white_pixels = cv2.countNonZero(thresh)
            total_pixels = gray.shape[0] * gray.shape[1]
            white_ratio = white_pixels / total_pixels
            
            # Also check for the specific button color/pattern
            # Look for the distinctive button background/outline
            hsv = cv2.cvtColor(button_region, cv2.COLOR_BGR2HSV)
            
            # Look for bright/white areas (button text)
            lower_white = np.array([0, 0, 200])
            upper_white = np.array([180, 30, 255])
            white_mask = cv2.inRange(hsv, lower_white, upper_white)
            white_area = cv2.countNonZero(white_mask) / total_pixels
            
            log(f"Button detection - White ratio: {white_ratio:.3f}, White area: {white_area:.3f}")
            
            # If we have significant white areas, likely the button is there
            if white_ratio > 0.05 or white_area > 0.05:
                return True
    
    return False

def get_continue_fishing_button_position(width, height):
    """
    Return the position to click for the 'Continue fishing' button
    Based on your screenshot, the button is roughly in the center-bottom
    """
    # Center of the button area - adjust these coordinates based on your actual button position
    button_center_x = 1200  # Adjust based on your screenshot
    button_center_y = 700   # Adjust based on your screenshot
    
    return get_scale_point((button_center_x, button_center_y), width, height)

def is_still_in_results_screen(img, width, height):
    """
    Check if we're still in the fish catch results screen
    by looking for characteristic elements like the fish name, size, etc.
    """
    # Check multiple areas that should be visible in results screen
    
    # 1. Check for the exit fishing button/text in top area
    exit_area = get_scale_area((1700, 50, 1850, 100), width, height)
    ex1, ey1, ex2, ey2 = exit_area
    if (ex1 >= 0 and ey1 >= 0 and ex2 <= img.shape[1] and ey2 <= img.shape[0]):
        exit_region = img[ey1:ey2, ex1:ex2]
        gray_exit = cv2.cvtColor(exit_region, cv2.COLOR_BGR2GRAY)
        _, thresh_exit = cv2.threshold(gray_exit, 200, 255, cv2.THRESH_BINARY)
        exit_white_ratio = cv2.countNonZero(thresh_exit) / (gray_exit.shape[0] * gray_exit.shape[1])
        
        # 2. Check for the fish info area
        fish_info_area = get_scale_area((800, 300, 1100, 400), width, height)
        fi1, fy1, fi2, fy2 = fish_info_area
        if (fi1 >= 0 and fy1 >= 0 and fi2 <= img.shape[1] and fy2 <= img.shape[0]):
            fish_region = img[fy1:fy2, fi1:fi2]
            gray_fish = cv2.cvtColor(fish_region, cv2.COLOR_BGR2GRAY)
            _, thresh_fish = cv2.threshold(gray_fish, 200, 255, cv2.THRESH_BINARY)
            fish_white_ratio = cv2.countNonZero(thresh_fish) / (gray_fish.shape[0] * gray_fish.shape[1])
            
            # If we have white text in both characteristic areas, we're likely in results screen
            if exit_white_ratio > 0.1 and fish_white_ratio > 0.1:
                return True
    
    return False


def get_search_region(center, offset):
    """
    Calculate search rectangle region based on center point and offset.
    :param center: (x, y) search region center coordinates
    :param offset: int search region radius (pixels)
    :return: (left, top, right, bottom)
    """
    return (
        center[0] - offset,
        center[1] - offset,
        center[0] + offset,
        center[1] + offset
    )

def get_scale_area(rect, cur_w, cur_h, base_w=1920, base_h=1080):
    x1, y1, x2, y2 = rect
    scale_x = cur_w / base_w
    scale_y = cur_h / base_h
    return (
        int(x1 * scale_x),
        int(y1 * scale_y),
        int(x2 * scale_x),
        int(y2 * scale_y)
    )

def get_scale_point(point, cur_w, cur_h, base_w=1920, base_h=1080):
    x, y = point
    scale_x = cur_w / base_w
    scale_y = cur_h / base_h
    return int(x * scale_x), int(y * scale_y)

def get_scale_val(val, cur_w, cur_h, base_w=1920, base_h=1080):
    scale_x = cur_w / base_w
    return val * scale_x

def get_int_scale_val(val, cur_w, cur_h, base_w=1920, base_h=1080):
    return int(get_scale_val(val, cur_w, cur_h, base_w, base_h))

def log(*args, sep=' ', end='\n'):
    """Print function with time prefix, supports multiple arguments"""
    now = datetime.now().strftime("[%H:%M:%S]")
    print(now, *args, sep=sep, end=end)

def find_target_window():
    """Find and return window object with exact title '星痕共鸣'"""
    all_windows = gw.getAllWindows()
    for w in all_windows:
        if w.title == "星痕共鸣":
            log("Successfully obtained target window")
            return w
    log("Game window not found")
    return None

def get_window_by_hwnd(hwnd):
    """Get window object by window handle"""
    try:
        return gw.Window(hWnd=hwnd)
    except Exception as e:
        log(f"Failed to get window: {e}")
        return None

def find_best_water_region(screenshot, fish_region, template_path, step=10):
    """
    In screenshot, around fish_region center point, horizontally slide template-width rectangle area, y unchanged, find best match.

    Parameters:
        screenshot: np.array, BGR image
        fish_region: (x, y, w, h)
        template_path: template path, read as grayscale
        step: horizontal sliding step size
        search_range: sliding range, in pixels, left and right by search_range pixels

    Returns:
        best_rect: (x, y, w, h)
        best_score: matching score
    """
    height, width = screenshot.shape[:2]
    step = get_int_scale_val(step, width, height)
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if template is None:
        raise FileNotFoundError(f"Template image not found: {template_path}")
    template_h, template_w = template.shape
    template_h = get_int_scale_val(template_h, width, height)
    template_w = get_int_scale_val(template_w, width, height)
    # Fish region center x-coordinate
    fish_center_x = fish_region[0] + fish_region[2] // 2
    # y coordinate fixed (can use fish_region[1] or more precise positioning, like center y minus half template height)
    y = fish_region[1]

    # First convert to grayscale for matchTemplate
    screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

    best_score = -1
    best_rect = None

    # Calculate left and right boundaries of sliding range, ensuring not exceeding screenshot boundaries
    x_start = 0
    
    x_end = width

    for x in range(x_start, x_end + 1, step):
        # Take 2 times height region
        multi = 2
        combined_region = screenshot_gray[y:y + multi * template_h, x:x + template_w]
        if combined_region.shape != (multi * template_h, template_w):
            continue

        white_mask = (combined_region > 210).astype(np.uint8)
        white_pixels = cv2.countNonZero(white_mask)
        total_pixels = combined_region.shape[0] * combined_region.shape[1]
        score = white_pixels / total_pixels

        if score > best_score:
            best_score = score
            best_rect = (x, y, template_w, 2 * template_h)
        

    # log(f"Best match: {best_rect}, score={best_score:.4f}")
    return best_rect, best_score