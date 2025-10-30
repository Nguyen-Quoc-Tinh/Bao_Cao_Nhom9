import pygame
import random
import os
import json

# --- 1. KHỞI TẠO PYGAME VÀ CÀI ĐẶT ---
pygame.init()
# --- AUDIO: khởi tạo mixer và load âm thanh từ thư mục sound ---
try:
    pygame.mixer.init()
    SOUND_DIR = os.path.join(os.path.dirname(__file__), "sound")

    def load_s(filename):
        p = os.path.join(SOUND_DIR, filename)
        if os.path.exists(p):
            try:
                return pygame.mixer.Sound(p)
            except Exception:
                return None
        return None

    s_paddle = load_s("paddle_hit_sound.wav")
    s_brick = load_s("brick_hit_sound.wav")
    s_powerup = load_s("powerup_sound.wav")
    s_life = load_s("marimba-lose-250960.wav")

    # load win sound (tìm winsoud.* trong thư mục sound với ext wav/mp3/ogg)
    s_win = None
    for ext in ("wav", "mp3", "ogg"):
        candidate = os.path.join(SOUND_DIR, f"winsoud.{ext}")
        if os.path.exists(candidate):
            try:
                s_win = pygame.mixer.Sound(candidate)
            except Exception:
                s_win = load_s(f"winsoud.{ext}")
            if s_win:
                s_win.set_volume(0.8)
                print(f"Loaded win sound: winsoud.{ext}")
                break
except Exception:
    s_paddle = s_brick = s_powerup = s_life = None

# Kích thước cửa sổ
WIDTH = 800
HEIGHT = 600

# Kích thước paddle mặc định
PADDLE_HEIGHT = 10
PADDLE_WIDTH_DEFAULT = 100

# Kích thước bóng
BALL_RADIUS = 10

# Màu sắc
BG_COLOR = (0, 0, 0)

# Màu thanh trượt và bóng
WHITE = (255, 255, 255)

# Màu nút
GREEN = (0, 170, 0)
RED = (170, 0, 0)
YELLOW = (200, 200, 0)
BLUE = (0, 0, 170)

# Màu nút khi hover
LIGHT_GREEN = (0, 200, 0)
LIGHT_RED = (200, 0, 0)
LIGHT_YELLOW = (255, 255, 50)
LIGHT_BLUE = (0, 0, 200)

# Màu Vật phẩm
POWERUP_COLOR = {
    "extend": (50, 255, 255),
    "life": (255, 50, 255),
    "slow": (50, 50, 255)
}

# Thời lượng vật phẩm (ms)
POWERUP_DURATION_MS = 5000

# Kích thước gạch và khoảng cách
BRICK_WIDTH = 68
BRICK_HEIGHT = 20
SPACING = 10

window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Brick Breaker - Game Phá Gạch")
clock = pygame.time.Clock()

# === PHẦN FONT TIẾNG VIỆT ===
try:
    FONT_FILE = "OpenSans-Regular.ttf" 
    font_path = os.path.join(os.path.dirname(__file__), FONT_FILE)
    font = pygame.font.Font(font_path, 24)
    big_font = pygame.font.Font(font_path, 48)
    title_font = pygame.font.Font(font_path, 72)
    print(f"Sử dụng font file thành công: {FONT_FILE}")
except: 
    print(f"LỖI: KHÔNG tìm thấy file font. Đang sử dụng font hệ thống.")
    font = pygame.font.SysFont("Arial Unicode MS", 24)
    big_font = pygame.font.SysFont("Arial Unicode MS", 48, bold=True)
    title_font = pygame.font.SysFont("Arial Unicode MS", 72, bold=True)

# --- LOAD ẢNH NỀN MENU (png/jpg/bmp trong image hoặc image/menu) ---
MENU_BG = None
try:
    base = os.path.dirname(__file__)
    candidates = [
        os.path.join(base, "image", "menu.png"),
        os.path.join(base, "image", "menu.jpg"),
        os.path.join(base, "image", "menu.bmp"),
        os.path.join(base, "image", "menu", "background.png"),
        os.path.join(base, "image", "menu", "background.jpg"),
        os.path.join(base, "image", "menu", "menu.png"),
        os.path.join(base, "image", "menu", "menu.jpg"),
    ]
    for p in candidates:
        if os.path.exists(p):
            # load image (ưu tiên alpha nếu có)
            try:
                img = pygame.image.load(p).convert_alpha()
            except Exception:
                img = pygame.image.load(p).convert()
            iw, ih = img.get_size()
            # scale giữ tỷ lệ theo chế độ "cover" (lấp đầy cửa sổ, có thể crop)
            scale = max(WIDTH / iw, HEIGHT / ih)
            new_w, new_h = int(iw * scale), int(ih * scale)
            try:
                scaled = pygame.transform.smoothscale(img, (new_w, new_h))
            except Exception:
                scaled = pygame.transform.scale(img, (new_w, new_h))
            # crop chính giữa để vừa cửa sổ
            x = (new_w - WIDTH) // 2
            y = (new_h - HEIGHT) // 2
            MENU_BG = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            MENU_BG.blit(scaled, (-x, -y))
            print(f"Đã load menu background (scaled & cropped): {p} -> {new_w}x{new_h}")
            break
except Exception as e:
    MENU_BG = None
    print("Không load được ảnh nền menu:", e)

# --- 2. HÀM HỖ TRỢ ---

## CÁC HÀM XỬ LÝ ĐIỂM SỐ
SCORES_FILE = "highscores.json"

def load_scores():
    try:
        with open(SCORES_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_scores(scores):
    scores.sort(key=lambda item: item['score'], reverse=True)
    with open(SCORES_FILE, 'w') as f:
        json.dump(scores, f, indent=4)

def is_high_score(score, scores):
    if len(scores) < 5:
        return True
    return score > scores[-1]['score']

def random_color():
    return (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))

def create_bricks(rows):
    temp_bricks = []
    cols = WIDTH // (BRICK_WIDTH + SPACING)
    for row in range(rows):
        for col in range(cols):
            total_brick_width = cols * (BRICK_WIDTH + SPACING) - SPACING
            start_x = (WIDTH - total_brick_width) // 2
            brick_x = start_x + col * (BRICK_WIDTH + SPACING)
            brick_y = 50 + row * (BRICK_HEIGHT + SPACING)
            rect = pygame.Rect(brick_x, brick_y, BRICK_WIDTH, BRICK_HEIGHT)
            color = random_color()
            temp_bricks.append((rect, color))
    return temp_bricks

def reset_game(difficulty):
    if difficulty == 'easy':
        lives, base_ball_speed, paddle_speed, brick_rows = 5, 4, 8, 4
    elif difficulty == 'hard':
        lives, base_ball_speed, paddle_speed, brick_rows = 2, 7, 9, 6
    else:  # 'medium'
        lives, base_ball_speed, paddle_speed, brick_rows = 3, 5, 7, 5
    
    return {
        "paddle_x": (WIDTH - PADDLE_WIDTH_DEFAULT) // 2, "paddle_y": HEIGHT - 50,
        "paddle_speed": paddle_speed, "paddle_width": PADDLE_WIDTH_DEFAULT,
        "ball_x": WIDTH // 2, "ball_y": HEIGHT // 2,
        "ball_x_speed": 0, "ball_y_speed": 0, "base_ball_speed": base_ball_speed, 
        "score": 0, "lives": lives, "level": 1, "bricks": create_bricks(brick_rows), 
        "waiting": True, "current_difficulty": difficulty, "powerups": [], "is_slowed": False,
        "active_powerups": []  # danh sách các powerup đang hoạt động với expiry time
    }

# --- XỬ LÝ VẬT PHẨM ---
def check_powerup_collision(game):
    paddle_rect = pygame.Rect(game["paddle_x"], game["paddle_y"], game["paddle_width"], PADDLE_HEIGHT)
    new_powerups = []
    for pu in game["powerups"]:
        pu_rect = pu["rect"]
        if pu_rect.colliderect(paddle_rect):
            apply_powerup(game, pu["type"])
        else:
            pu_rect.y += pu.get("speed", 3)
            if pu_rect.y < HEIGHT:
                new_powerups.append(pu)
    game["powerups"] = new_powerups

def apply_powerup(game, pu_type):
    now = pygame.time.get_ticks()
    game.setdefault("active_powerups", [])
    # life là instant và không cần hoàn tác
    if pu_type == "extend":
        # tăng kích thước paddle tạm thời
        game["paddle_width"] = min(200, game["paddle_width"] + 50)
        game["paddle_x"] = max(0, game["paddle_x"] - 25) 
        game["active_powerups"].append({"type": "extend", "expiry": now + POWERUP_DURATION_MS})
    elif pu_type == "life":
        game["lives"] += 1
    elif pu_type == "slow":
        # nếu đã slowed thì vẫn tạo 1 bản ghi mới (kéo dài hiệu lực)
        if not game.get("is_slowed", False):
            game["is_slowed"] = True
            if game["ball_x_speed"] != 0 or game["ball_y_speed"] != 0:
                game["ball_x_speed"] /= 1.5
                game["ball_y_speed"] /= 1.5
        game["active_powerups"].append({"type": "slow", "expiry": now + POWERUP_DURATION_MS})
    try:
        if s_powerup:
            s_powerup.play()
    except Exception:
        pass
def update_active_powerups(game):
    """Kiểm tra các powerup đang hoạt động, revert khi hết hạn."""
    now = pygame.time.get_ticks()
    new_active = []
    for ap in game.get("active_powerups", []):
        if ap["expiry"] <= now:
            # hoàn tác theo loại
            if ap["type"] == "extend":
                # giảm kích thước paddle đã tăng (không xuống dưới mặc định)
                game["paddle_width"] = max(PADDLE_WIDTH_DEFAULT, game["paddle_width"] - 50)
                game["paddle_x"] = min(game["paddle_x"], WIDTH - game["paddle_width"])
            elif ap["type"] == "slow":
                # nếu không còn đoạn slow nào khác thì mở lại tốc độ
                # kiểm tra còn các slow khác chưa hết hạn
                still_slow = any(x["type"] == "slow" and x["expiry"] > now for x in game.get("active_powerups", []))
                if not still_slow and game.get("is_slowed", False):
                    game["is_slowed"] = False
                    if game["ball_x_speed"] != 0 or game["ball_y_speed"] != 0:
                        game["ball_x_speed"] *= 1.5
                        game["ball_y_speed"] *= 1.5
            # life không cần revert
        else:
            new_active.append(ap)
    game["active_powerups"] = new_active
# --- HÀM VẼ ---
def draw_powerups(game):
    for pu in game["powerups"]:
        pygame.draw.rect(window, POWERUP_COLOR[pu["type"]], pu["rect"])
        if pu["type"] == "extend": text_char = "+"
        elif pu["type"] == "life": text_char = "♥"
        else: text_char = "S"
        pu_font = pygame.font.SysFont(None, 20) 
        pu_text = pu_font.render(text_char, True, WHITE)
        window.blit(pu_text, (pu["rect"].x + 5, pu["rect"].y + 2))

def draw_menu_buttons(mouse_pos, buttons):
    def text_color_for_bg(color):
        r, g, b = color
        # độ sáng (luminance) để quyết định màu chữ cho tương phản
        luminance = 0.299 * r + 0.587 * g + 0.114 * b
        return (0, 0, 0) if luminance > 180 else WHITE

    for text, (button, active_color, inactive_color) in buttons.items():
        color = active_color if button.collidepoint(mouse_pos) else inactive_color
        pygame.draw.rect(window, color, button)
        text_color = text_color_for_bg(color)
        text_surf = font.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=button.center)
        window.blit(text_surf, text_rect)

def draw_menu_background(dim=120):
    """Vẽ ảnh nền menu (MENU_BG) và phủ lớp mờ (dim) để chữ/menu dễ đọc.
    dim: 0..255 alpha của phủ đen (mặc định 120)."""
    if MENU_BG:
        # MENU_BG đã được scale lúc load; đảm bảo kích thước bằng cửa sổ
        window.blit(MENU_BG, (0, 0))
        if dim > 0:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, dim))
            window.blit(overlay, (0, 0))
    else:
        window.fill(BG_COLOR)

def draw_pause_menu(mouse_pos):
    # Giữ nguyên overlay pause, nhưng nếu muốn có nền menu thay cho game có thể gọi draw_menu_background()
    # (hiện code gọi draw_game_screen trước khi vẽ pause overlay, nên giữ như cũ)
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    window.blit(overlay, (0, 0))
    pause_text = title_font.render("TẠM DỪNG", True, WHITE)
    window.blit(pause_text, (WIDTH//2 - pause_text.get_width()//2, HEIGHT//6))
    buttons = {
        "Back To Game": (continue_button, LIGHT_BLUE, BLUE),
        "Restart Level": (restart_button, LIGHT_YELLOW, YELLOW),
        "Main Menu": (quit_pause_button, LIGHT_RED, RED)
    }
    draw_menu_buttons(mouse_pos, buttons)

def draw_menu(mouse_pos):
    # dùng ảnh nền menu + dim để chữ dễ đọc
    draw_menu_background(dim=120)
    title_text = title_font.render("BRICK BREAKER", True, WHITE)
    window.blit(title_text, (WIDTH//2 - title_text.get_width()//2, 100))
    
    player_greeting = font.render(f"Welcome, {current_player_name}!", True, YELLOW)
    window.blit(player_greeting, (WIDTH//2 - player_greeting.get_width()//2, 200))

    buttons = {
        "Start Game": (start_button, LIGHT_GREEN, GREEN),
        "High Scores": (scores_button, LIGHT_YELLOW, YELLOW),
        "Change Player": (change_player_button, LIGHT_BLUE, BLUE),
        "Quit": (quit_button, LIGHT_RED, RED)
    }
    draw_menu_buttons(mouse_pos, buttons)

def draw_difficulty_screen(mouse_pos):
    # dùng cùng nền menu để giữ thống nhất
    draw_menu_background(dim=140)
    title_text = big_font.render("Chọn Độ Khó", True, WHITE)
    window.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 4))
    buttons = {
        "Easy (5 Lives)": (easy_button, LIGHT_GREEN, GREEN),
        "Medium (3 Lives)": (medium_button, LIGHT_YELLOW, YELLOW),
        "Hard (2 Lives)": (hard_button, LIGHT_RED, RED),
        "Back": (back_button, LIGHT_BLUE, BLUE)
    }
    draw_menu_buttons(mouse_pos, buttons)

def draw_game_screen(game, player_name):
    window.fill(BG_COLOR)
    for brick, color in game["bricks"]:
        pygame.draw.rect(window, color, brick)
    pygame.draw.rect(window, WHITE, (game["paddle_x"], game["paddle_y"], game["paddle_width"], PADDLE_HEIGHT))
    pygame.draw.circle(window, WHITE, (int(game["ball_x"]), int(game["ball_y"])), BALL_RADIUS)
    draw_powerups(game)
    
    player_text = font.render(player_name, True, YELLOW)
    window.blit(player_text, (10, 10))

    score_text = font.render(f"Score: {game['score']}", True, WHITE)
    lives_text = font.render(f"Lives: {game['lives']}", True, WHITE)
    level_text = font.render(f"Level: {game['level']}", True, WHITE)
    window.blit(score_text, (10, 40))
    window.blit(lives_text, (WIDTH - lives_text.get_width() - 10, 10))
    window.blit(level_text, (WIDTH//2 - level_text.get_width()//2, 10))
    
    if game["waiting"]:
        msg = font.render(f"Level {game['level']} - Press SPACE to launch ball", True, WHITE) 
        window.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2))

def draw_game_over_screen(final_score): 
    window.fill(BG_COLOR)
    over_text = big_font.render("GAME OVER", True, (255, 0, 0))
    score_msg = font.render(f"Final Score: {final_score}", True, WHITE)
    restart_msg = font.render("Press R for Menu or Q to Quit", True, WHITE)
    
    window.blit(over_text, (WIDTH//2 - over_text.get_width()//2, HEIGHT//2 - 60))
    window.blit(score_msg, (WIDTH//2 - score_msg.get_width()//2, HEIGHT//2))
    window.blit(restart_msg, (WIDTH//2 - restart_msg.get_width()//2, HEIGHT//2 + 40))

def draw_enter_name_start_screen(player_name):
    draw_menu_background(dim=140)
    title_text = big_font.render("WELCOME!", True, YELLOW)
    prompt_text = font.render("Enter your name (3-10 chars):", True, WHITE)
    
    window.blit(title_text, (WIDTH//2 - title_text.get_width()//2, HEIGHT//4))
    window.blit(prompt_text, (WIDTH//2 - prompt_text.get_width()//2, HEIGHT//2 - 50))

    input_box = pygame.Rect(WIDTH//2 - 150, HEIGHT//2, 300, 50)
    pygame.draw.rect(window, WHITE, input_box, 2)
    
    name_surf = big_font.render(player_name, True, WHITE)
    text_y = input_box.y + (input_box.height - name_surf.get_height()) // 2
    window.blit(name_surf, (input_box.x + 10, text_y))
    
    info_text = font.render("Press ENTER to continue", True, WHITE)
    window.blit(info_text, (WIDTH//2 - info_text.get_width()//2, HEIGHT - 100))

def draw_high_scores_screen(scores, mouse_pos):
    draw_menu_background(dim=140)
    title_text = big_font.render("HIGH SCORES", True, YELLOW)
    window.blit(title_text, (WIDTH//2 - title_text.get_width()//2, 50))

    start_y = 150
    for i, entry in enumerate(scores):
        rank_text = font.render(f"{i+1}.", True, WHITE)
        name_text = font.render(entry['name'], True, WHITE)
        score_text = font.render(str(entry['score']), True, WHITE)
        
        window.blit(rank_text, (200, start_y + i * 50))
        window.blit(name_text, (250, start_y + i * 50))
        window.blit(score_text, (500, start_y + i * 50))
        
    buttons = {"Back to Menu": (back_to_menu_button, LIGHT_BLUE, BLUE)}
    draw_menu_buttons(mouse_pos, buttons)

# --- 3. BIẾN GAME BAN ĐẦU ---
game = {} 
running = True
game_state = "enter_name_start" 
current_player_name = ""
high_scores = load_scores()


# Định nghĩa các nút 
start_button = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 - 60, 200, 50) ## SỬA
scores_button = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 10, 200, 50) ## SỬA
change_player_button = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 80, 200, 50) ## MỚI
quit_button = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 150, 200, 50) ## SỬA
easy_button = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 - 60, 200, 50)
medium_button = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 10, 200, 50)
hard_button = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 80, 200, 50)
back_button = pygame.Rect(30, 30, 150, 40)
continue_button = pygame.Rect(WIDTH//2 - 120, HEIGHT//2 - 80, 240, 60)
restart_button = pygame.Rect(WIDTH//2 - 120, HEIGHT//2 + 0, 240, 60)
quit_pause_button = pygame.Rect(WIDTH//2 - 120, HEIGHT//2 + 80, 240, 60)
back_to_menu_button = pygame.Rect(WIDTH//2 - 120, HEIGHT - 100, 240, 50)

# --- 4. VÒNG LẶP GAME ---
while running:
    clock.tick(60)
    mouse_pos = pygame.mouse.get_pos()

    # --- XỬ LÝ SỰ KIỆN (INPUT) ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if game_state == "playing": game_state = "paused"
            elif game_state == "paused": game_state = "playing"

        if game_state == "enter_name_start":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and len(current_player_name) >= 3:
                    game_state = "menu"
                elif event.key == pygame.K_BACKSPACE:
                    current_player_name = current_player_name[:-1]
                else:
                    if len(current_player_name) < 10 and event.unicode.isalnum():
                        current_player_name += event.unicode

        elif game_state == "menu":
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.collidepoint(event.pos): 
                    game_state = "select_difficulty" 
                if scores_button.collidepoint(event.pos): 
                    game_state = "high_scores"
                if change_player_button.collidepoint(event.pos): ## SỬA
                    game_state = "enter_name_start"
                    current_player_name = ""
                if quit_button.collidepoint(event.pos): 
                    running = False
        
        elif game_state == "select_difficulty":
            if event.type == pygame.MOUSEBUTTONDOWN:
                difficulty = None
                if easy_button.collidepoint(event.pos): difficulty = 'easy'
                elif medium_button.collidepoint(event.pos): difficulty = 'medium'
                elif hard_button.collidepoint(event.pos): difficulty = 'hard'
                elif back_button.collidepoint(event.pos): game_state = "menu"
                if difficulty:
                    game = reset_game(difficulty) 
                    game_state = "playing" 
        
        elif game_state == "playing":
            if game["waiting"] and event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                speed = game["base_ball_speed"] + game["level"] * 0.5 
                game["ball_x_speed"] = speed
                game["ball_y_speed"] = -speed
                game["waiting"] = False
        
        elif game_state == "paused":
            if event.type == pygame.MOUSEBUTTONDOWN:
                if continue_button.collidepoint(event.pos): game_state = "playing"
                elif restart_button.collidepoint(event.pos):
                    game = reset_game(game["current_difficulty"])
                    game_state = "playing"
                elif quit_pause_button.collidepoint(event.pos): game_state = "menu"
        
        elif game_state == "game_over":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r: game_state = "menu"
                if event.key == pygame.K_q: running = False
        
        elif game_state == "high_scores":
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_to_menu_button.collidepoint(event.pos):
                    game_state = "menu"

    # --- LOGIC GAME ---
    if game_state == "playing":
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: game["paddle_x"] -= game["paddle_speed"]
        if keys[pygame.K_RIGHT]: game["paddle_x"] += game["paddle_speed"]
        game["paddle_x"] = max(0, min(game["paddle_x"], WIDTH - game["paddle_width"]))
        
        if not game["waiting"]:
            ball_speed_multiplier = 0.66 if game.get("is_slowed") else 1.0
            game["ball_x"] += game["ball_x_speed"] * ball_speed_multiplier
            game["ball_y"] += game["ball_y_speed"] * ball_speed_multiplier
            check_powerup_collision(game)

            # cập nhật powerup đang hoạt động (revert khi hết hạn)
            update_active_powerups(game)

            if game["ball_x"] >= WIDTH - BALL_RADIUS:
                game["ball_x_speed"] *= -1
                game["ball_x"] = WIDTH - BALL_RADIUS
            elif game["ball_x"] <= BALL_RADIUS:
                game["ball_x_speed"] *= -1
                game["ball_x"] = BALL_RADIUS
            if game["ball_y"] <= BALL_RADIUS: 
                game["ball_y_speed"] *= -1
                game["ball_y"] = BALL_RADIUS

            paddle_rect = pygame.Rect(game["paddle_x"], game["paddle_y"], game["paddle_width"], PADDLE_HEIGHT)
            ball_rect = pygame.Rect(game["ball_x"] - BALL_RADIUS, game["ball_y"] - BALL_RADIUS, BALL_RADIUS * 2, BALL_RADIUS * 2)
            if ball_rect.colliderect(paddle_rect) and game["ball_y_speed"] > 0:
                # phản xạ cơ bản và điều chỉnh hướng theo vị trí chạm
                offset = (game["ball_x"] - (game["paddle_x"] + game["paddle_width"] / 2)) / (game["paddle_width"] / 2)
                speed = max(abs(game.get("ball_x_speed", 0)), game["base_ball_speed"])
                game["ball_x_speed"] = offset * speed
                game["ball_y_speed"] *= -1
                game["ball_y"] = game["paddle_y"] - BALL_RADIUS
                try:
                    if s_paddle:
                        s_paddle.play()
                except Exception:
                    pass

            for i, (brick, color) in enumerate(game["bricks"]):
                if ball_rect.colliderect(brick):
                    game["score"] += 10
                    del game["bricks"][i]
                    game["ball_y_speed"] *= -1
                    try:
                        if s_brick:
                            s_brick.play()
                    except Exception:
                        pass
                    # ngẫu nhiên spawn powerup
                    if random.random() < 0.12:
                        pu_type = random.choice(list(POWERUP_COLOR.keys()))
                        pu_rect = pygame.Rect(brick.x + (brick.width - 20)//2, brick.y, 20, 20)
                        game["powerups"].append({"rect": pu_rect, "type": pu_type, "speed": 3})
                    break
            
            if game["ball_y"] > HEIGHT:
                game["lives"] -= 1
                try:
                    if s_life:
                        s_life.play()
                except Exception:
                    pass
                if game["lives"] > 0:
                    game["waiting"] = True
                    game["ball_x"] = WIDTH // 2
                    game["ball_y"] = HEIGHT // 2
                    game["ball_x_speed"] = 0
                    game["ball_y_speed"] = 0
                else:
                    high_scores.append({"name": current_player_name, "score": game["score"]})
                    save_scores(high_scores)
                    game_state = "game_over"

            if not game["bricks"]:
                # play win sound (nếu có)
                try:
                    if s_win:
                        s_win.play()
                except Exception:
                    pass
                game["level"] += 1
                game["base_ball_speed"] += 0.5
                game["bricks"] = create_bricks(4 + min(game["level"], 4))
                game["waiting"] = True
                game["ball_x"], game["ball_y"] = WIDTH // 2, HEIGHT // 2
                game["ball_x_speed"] = game["ball_y_speed"] = 0
    # --- VẼ LÊN MÀN HÌNH ---
    if game_state == "enter_name_start":
        draw_enter_name_start_screen(current_player_name)
    elif game_state == "menu":
        draw_menu(mouse_pos)
    elif game_state == "select_difficulty":
        draw_difficulty_screen(mouse_pos)
    elif game_state == "playing":
        draw_game_screen(game, current_player_name)
    elif game_state == "paused":
        draw_game_screen(game, current_player_name)
        draw_pause_menu(mouse_pos)
    elif game_state == "game_over":
        draw_game_over_screen(game.get('score', 0))
    elif game_state == "high_scores":
        draw_high_scores_screen(high_scores, mouse_pos)
    pygame.display.flip()
pygame.quit()