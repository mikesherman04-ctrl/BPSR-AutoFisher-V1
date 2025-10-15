# config.py

# ====== Basic Parameters ======
PROCESS_NAME = "BPSR_STEAM.exe"             # Process name to automate
LOG_DIR = "log"                       # Screenshot and log save directory
CAPTURE_SCREENSHOT = False            # Whether to save screenshots each round (for debugging)

# ====== Operation Coordinates ======
CLICK_POS = (922, 380)                # Click position for casting hook/hooking (in-window coordinates)
SECOND_CLICK_POS = (1600, 1010)       # Click position after fishing completion (in-window coordinates)

# ====== Red Dot Detection Parameters ======
# Automatic red dot search in large area (center ± offset range), center should be expected float area, larger offset means larger search range
RED_SEARCH_REGION_CENTER = (922, 383)            # Red dot search region center
XuanYa = (922, 600)         # Red dot search region center (cliff area)
RED_SEARCH_REGION_OFFSET = 100                # Search region radius (pixels)
RED_SEARCH_REGION_RECT = (                    # Large red dot search area (top-left x, top-left y, bottom-right x, bottom-right y)
    RED_SEARCH_REGION_CENTER[0] - RED_SEARCH_REGION_OFFSET,
    RED_SEARCH_REGION_CENTER[1] - RED_SEARCH_REGION_OFFSET,
    RED_SEARCH_REGION_CENTER[0] + RED_SEARCH_REGION_OFFSET,
    RED_SEARCH_REGION_CENTER[1] + RED_SEARCH_REGION_OFFSET
)
RED_DETECT_BOX_SIZE = 7             # Red dot detection small square side length (pixels, recommended 7)
RED_THRESHOLD = 0.6                 # Threshold for determining red pixel ratio
RED_NOT_FOUND_TIME = 0.7          # How long red dot disappears before determining "hooked" (seconds)

# ====== Fishing Completion Detection Parameters (Gray Area) ======
COLOR_CHECK_AREA = (1454, 980, 1520, 1003)    # Gray area for determining fishing completion (in-window coordinates)
TARGET_COLOR = (232, 232, 232)                # Target color (RGB) this area should be when fishing is complete

# ====== Delay Parameters ======
START_DELAY = 5                    # Initial delay after casting hook (seconds)
AFTER_SECOND_CLICK_DELAY = 3       # Wait time after clicking SECOND_CLICK_POS when fishing completes (seconds)

# ====== Level Detection (Fish Escaped Detection) ======
BLUE_ROI = (1178, 989, 1225, 1019) # Cyan area for detecting fish escape (in-window coordinates)
BLUE_COLORS = [                    # Target cyan colors for determining "fish escaped"
    (41, 140, 149),
    (31, 117, 133),
    (31, 114, 131),
    (34, 119, 134),
    (36, 126, 139),
]
BLUE_TOLERANCE = 15                 # Color tolerance

# ====== Mouse Event Codes ======
MOUSEEVENTF_LEFTDOWN = 0x0002      # Mouse left button down event code
MOUSEEVENTF_LEFTUP = 0x0004        # Mouse left button up event code

# ====== A/D Key Judgment Parameters ======
POINT_A_POS = (938, 540)           # Check point for "A" key (in-window coordinates)
POINT_D_POS = (982, 540)           # Check point for "D" key (in-window coordinates)
POINT_CHECK_COLORS = [             # Target colors for "A/D" judgment
    (216, 209, 196),
    (237, 243, 247),
    (219, 211, 197)
]
POINT_CHECK_TOLERANCE = 20         # "A/D" color tolerance
POINT_REGION_OFFSET = 2            # Detection area range (check point ± pixels)
POINT_REGION_RATIO = 0.5           # Threshold for target color ratio in detection area

# ====== Durability Check After Casting ======
POST_CAST_CHECK_RECT = (1641, 1024, 1660, 1039)    # Durability check area after casting
POST_CAST_COLORS = [                               # Target colors when fishing rod has no durability
    (137, 145, 153),
    (131, 138, 145),
    (95, 101, 107),
    (95, 102, 107),
]
POST_CAST_TOLERANCE = 20                           # Color tolerance
POST_CAST_RATIO = 0.5                              # Threshold for matching target color pixel ratio

# ====== Fishing Rod No Durability Handling Parameters ======
ROD_NO_DURABILITY_KEY = "m"        # Key to press when fishing rod has no durability
ROD_CHANGE_CLICK_POS = (1722, 595) # Fishing rod replacement click position
ROD_CONFIRM_CLICK_POS = (750, 300) # Confirmation click position after rod replacement
ROD_NO_DURABILITY_DELAY = 1        # Wait time between each operation (seconds)

# ====== Click Delay After Fishing Completion (seconds) (New, controls click speed) ======
AFTER_DETECT_CLICK_DELAY = 1    # Delay between detecting fishing completion and clicking SECOND_CLICK_POS, smaller value means faster

# ====== Continue Fishing Button Detection ======
CONTINUE_FISHING_BUTTON_AREA = (1000, 650, 1400, 750)  # Area to search for the button
CONTINUE_FISHING_CLICK_POS = (1200, 700)  # Position to click for continue fishing button
CONTINUE_FISHING_MAX_WAIT = 5  # Maximum seconds to wait for the button