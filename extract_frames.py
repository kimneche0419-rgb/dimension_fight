import cv2
import numpy as np
import os
import glob

def load_image_unicode(path):
    stream = open(path, 'rb')
    bytes = bytearray(stream.read())
    numpyarray = np.asarray(bytes, dtype=np.uint8)
    return cv2.imdecode(numpyarray, cv2.IMREAD_UNCHANGED)

def save_image_unicode(path, img):
    ext = os.path.splitext(path)[1]
    result, n = cv2.imencode(ext, img)
    if result:
        with open(path, mode='wb') as f:
            n.tofile(f)

ships = ["전투기.png", "순양함.png", "스텔스.png", "드레드노트.png", "심해함.png", "팬텀.png"]

os.makedirs('assets_frames', exist_ok=True)

for ship in ships:
    if not os.path.exists(ship):
        continue
    img = load_image_unicode(ship)
    if img is None: continue
    h, w = img.shape[:2]
    crop_y = int(h * 0.75)
    bottom = img[crop_y:, :]
    
    gray = cv2.cvtColor(bottom, cv2.COLOR_BGRA2GRAY) if img.shape[2] == 4 else cv2.cvtColor(bottom, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    boxes = []
    for c in contours:
        cx, cy, cw, ch = cv2.boundingRect(c)
        if cw > 50 and ch > 30 and cw < w//2:
            boxes.append((cx, cy, cw, ch))
    boxes.sort(key=lambda b: b[0])
    
    if len(boxes) < 4:
        continue
        
    boxes = boxes[-4:] 
    
    max_h = max(b[3] for b in boxes)
    max_w = max(b[2] for b in boxes)
    sz = max(max_w, max_h) + 20
    if sz % 2 != 0: sz += 1
    
    ship_name = os.path.splitext(ship)[0]
    
    for i, (bx, by, bw, bh) in enumerate(boxes):
        nose_x = bx + bw
        cy = by + bh // 2
        
        canvas = np.zeros((sz, sz, 4), dtype=np.uint8)
        
        src_x1 = nose_x - sz + 10
        src_x2 = nose_x + 10
        src_y1 = cy - sz // 2
        src_y2 = cy + sz // 2
        
        dst_x1 = 0
        dst_x2 = sz
        dst_y1 = 0
        dst_y2 = sz
        
        if src_x1 < 0:
            dst_x1 -= src_x1
            src_x1 = 0
        if src_y1 < 0:
            dst_y1 -= src_y1
            src_y1 = 0
        if src_x2 > bottom.shape[1]:
            dst_x2 -= (src_x2 - bottom.shape[1])
            src_x2 = bottom.shape[1]
        if src_y2 > bottom.shape[0]:
            dst_y2 -= (src_y2 - bottom.shape[0])
            src_y2 = bottom.shape[0]
            
        region = bottom[src_y1:src_y2, src_x1:src_x2]
        if region.shape[2] == 3:
            region = cv2.cvtColor(region, cv2.COLOR_BGR2BGRA)
        canvas[dst_y1:dst_y2, dst_x1:dst_x2] = region
        
        canvas_rot = cv2.rotate(canvas, cv2.ROTATE_90_COUNTERCLOCKWISE)
        
        bg_col = bottom[0,0]
        diff = np.abs(canvas_rot[:, :, :3].astype(np.int32) - bg_col[:3].astype(np.int32))
        mask = np.all(diff < 20, axis=2)
        canvas_rot[mask, 3] = 0
        
        # Trim transparent edges to make image compact? 
        # No, keeping size uniform is good for animation alignment.
        # However, the canvas is sz x sz (around 200x200). 
        # The game expects 36x36 or 72x72. We'll resize in pygame.
        out_path = f"assets_frames/{ship_name}_{i}.png"
        save_image_unicode(out_path, canvas_rot)
        
    print(f"Processed {ship_name}")
