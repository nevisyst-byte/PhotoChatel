import pygame
import os
import sys
import io
import threading
from pathlib import Path
import settings
import menu
from picamera2 import Picamera2
from datetime import datetime
import numpy as np
from time import sleep, time
import math
import cv2
import qrcode as qrcode_lib

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / "credentials"))

AWB_MODES = {
    "auto": 0,
    "manual": 1,
    "daylight": 2,
    "cloudy": 3,
    "tungsten": 4,
    "fluorescent": 5,
    "incandescent": 6,
    "flash": 7,
    "horizon": 8
}

pygame.init()
MARGIN = 20
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("ChatelRetroMobile Photobooth")
clock = pygame.time.Clock()

font_countdown_big = pygame.font.Font(str(BASE_DIR / "assets" / "GreatVibes-Regular.ttf"), 150)
font_countdown     = pygame.font.Font(str(BASE_DIR / "assets" / "GreatVibes-Regular.ttf"), 72)
font_label         = pygame.font.SysFont(None, 24)
font_caption       = pygame.font.SysFont(None, 24)
font_confirmation  = pygame.font.SysFont(None, 36)
font_counter       = pygame.font.SysFont(None, 30)
font_cta           = pygame.font.SysFont(None, 42)
font_event         = pygame.font.Font(str(BASE_DIR / "assets" / "GreatVibes-Regular.ttf"), 42)

user_settings = settings.load_settings()

frame_overlay_raw = pygame.image.load(str(BASE_DIR / "assets" / "frame_retro.png"))
frame_overlay = pygame.transform.smoothscale(frame_overlay_raw.convert_alpha(), screen.get_size())

icon_photo_base = pygame.image.load(str(BASE_DIR / "assets" / "icon_photo.png")).convert_alpha()
icon_photo = pygame.transform.scale(icon_photo_base, (150, 150))  # taille de base
button_enregistrer = pygame.image.load(str(BASE_DIR / "assets" / "button_enregistrer.png")).convert_alpha()
button_enregistrer = pygame.transform.smoothscale(button_enregistrer, (250, 90))
button_recommencer = pygame.image.load(str(BASE_DIR / "assets" / "button_recommencer.png")).convert_alpha()
button_recommencer = pygame.transform.smoothscale(button_recommencer, (250, 90))

base_save_path = BASE_DIR / "photos"
today_folder = datetime.now().strftime("%Y-%m-%d")
save_path = base_save_path / today_folder
os.makedirs(save_path, exist_ok=True)

photo_count = len([f for f in os.listdir(save_path) if f.endswith('.jpg')])

picam = Picamera2()
from libcamera import Transform

preview_config = picam.create_preview_configuration(
    main={"format": "YUV420", "size": (1920, 1080)},
    transform=Transform(hflip=1, vflip=0)
)

picam.configure(preview_config)

from libcamera import controls

picam.set_controls({
    "AfMode": 2,
    "AfTrigger": 0,
    "AwbEnable": True,
    "AwbMode": AWB_MODES["cloudy"],
    "AeEnable": True
})

picam.start()
sleep(2)
metadata = picam.capture_metadata()
gains = metadata.get("ColourGains", (1.0, 1.0))

picam.set_controls({
    "AwbEnable": False,
    "ColourGains": gains
})


def build_qr_surface(url):
    if not url or not url.startswith("http"):
        return None
    try:
        qr = qrcode_lib.QRCode(box_size=10, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        surf = pygame.image.load(buf)
        return pygame.transform.scale(surf, (300, 300))
    except Exception as e:
        print(f"QR error: {e}")
        return None


def upload_in_background(filepath, album_name):
    try:
        import google_photos_uploader
        google_photos_uploader.upload_photo(filepath, album_name)
    except Exception as e:
        print(f"Upload error: {e}")


def yuv420_to_rgb(yuv_frame):
    h, w = 1080, 1920
    yuv = yuv_frame.reshape((h * 3 // 2, w)).astype(np.uint8)
    rgb = cv2.cvtColor(yuv, cv2.COLOR_YUV2RGB_I420)
    rgb = np.rot90(rgb)
    return rgb


def get_video_rect():
    W, H = screen.get_width(), screen.get_height()
    x = int(W * 0.077)
    y = int(H * 0.289)
    w = int(W * 0.857)
    h = int(H * 0.430)
    return pygame.Rect(x, y, w, h)


def draw_video_frame(fullscreen=False):
    yuv_frame = picam.capture_array("main")
    frame = yuv420_to_rgb(yuv_frame)

    frame_surface = pygame.surfarray.make_surface(frame)
    if fullscreen:
        frame_surface = pygame.transform.scale(frame_surface, screen.get_size())
        screen.blit(frame_surface, (0, 0))
    else:
        vr = get_video_rect()
        frame_surface = pygame.transform.scale(frame_surface, (vr.width, vr.height))
        screen.blit(frame_surface, vr.topleft)


def show_live_countdown(delay):
    start_time = time()
    current_count = delay
    while current_count > 0:
        elapsed = int(time() - start_time)
        new_count = delay - elapsed
        if new_count != current_count:
            current_count = new_count

        draw_video_frame(fullscreen=True)
        count_text = font_countdown_big.render(str(current_count), True, (255, 255, 255))
        screen.blit(count_text, (
            screen.get_width() // 2 - count_text.get_width() // 2,
            screen.get_height() // 2 - count_text.get_height() // 2
        ))
        pygame.display.flip()
        clock.tick(30)


def show_qr_code(qr_surface, album_url):
    start = time()
    while time() - start < 6:
        screen.fill((10, 10, 10))
        qr_x = screen.get_width() // 2 - 150
        qr_y = screen.get_height() // 2 - 190
        screen.blit(qr_surface, (qr_x, qr_y))

        msg1 = font_confirmation.render("Photo enregistrée !", True, (255, 255, 255))
        screen.blit(msg1, (screen.get_width() // 2 - msg1.get_width() // 2, qr_y - 65))

        msg2 = font_confirmation.render("Retrouvez votre photo :", True, (200, 200, 200))
        screen.blit(msg2, (screen.get_width() // 2 - msg2.get_width() // 2, qr_y - 30))

        hint = font_label.render("Scannez avec votre téléphone  —  appuyez pour continuer", True, (130, 130, 130))
        screen.blit(hint, (screen.get_width() // 2 - hint.get_width() // 2, qr_y + 315))

        pygame.display.flip()
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN:
                return


def add_watermark(filepath):
    """D — Watermark : nom de l'événement + date en bas à droite de la photo."""
    from PIL import Image, ImageDraw, ImageFont as PILFont
    event_name = user_settings.get("event_name", "")
    date_str   = datetime.now().strftime("%d/%m/%Y")
    text       = f"{event_name}  •  {date_str}" if event_name else date_str
    try:
        img  = Image.open(str(filepath)).convert('RGB')
        draw = ImageDraw.Draw(img)
        W, H = img.size
        try:
            font = PILFont.truetype(str(BASE_DIR / "assets" / "GreatVibes-Regular.ttf"), 60)
        except Exception:
            font = PILFont.load_default()
        bbox     = draw.textbbox((0, 0), text, font=font)
        tw, th   = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x, y     = W - tw - 30, H - th - 30
        draw.text((x + 3, y + 3), text, fill=(0, 0, 0),       font=font)
        draw.text((x,     y),     text, fill=(255, 243, 200),  font=font)
        img.save(str(filepath), quality=95)
    except Exception as e:
        print(f"Watermark error: {e}")


def take_photo():
    global photo_count
    delay = int(user_settings.get("delay", 3))
    show_live_countdown(delay)

    screen.fill((255, 255, 255))
    pygame.display.flip()
    pygame.time.wait(150)
    filename = datetime.now().strftime("photo_%Y%m%d_%H%M%S.jpg")
    filepath = save_path / filename

    picam.stop()
    capture_config = picam.create_still_configuration(main={"size": (1920, 1080)})
    picam.configure(capture_config)
    picam.set_controls({"AwbEnable": False, "ColourGains": gains})
    picam.start()
    sleep(1.5)
    picam.capture_file(str(filepath))
    picam.stop()
    picam.configure(preview_config)
    picam.start()
    picam.set_controls({"AwbEnable": False, "ColourGains": gains})

    # D — Watermark
    add_watermark(filepath)

    try:
        vr           = get_video_rect()
        photo_orig   = pygame.image.load(str(filepath))
        photo_framed = pygame.transform.smoothscale(photo_orig, (vr.width, vr.height))
    except Exception:
        screen.fill((0, 0, 0))
        error_msg = font_confirmation.render("Erreur lors du chargement de la photo", True, (255, 0, 0))
        screen.blit(error_msg, (screen.get_width() // 2 - error_msg.get_width() // 2, 250))
        pygame.display.flip()
        pygame.time.wait(2000)
        return

    AUTO_SAVE = 15
    W, H     = screen.get_width(), screen.get_height()
    top_h    = int(H * 0.14)
    bot_h    = int(H * 0.22)

    bw, bh   = 250, 75
    bspace   = 50
    bx       = (W - bw * 2 - bspace) // 2
    by       = H - bh - 20
    keep_rect  = pygame.Rect(bx,             by, bw, bh)
    retry_rect = pygame.Rect(bx + bw + bspace, by, bw, bh)

    photo_full = pygame.transform.smoothscale(photo_orig, (W, H))

    # Dégradés pré-calculés
    top_grad = pygame.Surface((W, top_h), pygame.SRCALPHA)
    for i in range(top_h):
        a = int(200 * (1 - i / top_h))
        pygame.draw.rect(top_grad, (10, 5, 0, a), (0, i, W, 1))

    bot_grad = pygame.Surface((W, bot_h), pygame.SRCALPHA)
    for i in range(bot_h):
        # Opaque dès 40% de la hauteur du bandeau, puis 255
        t = min(1.0, (i / bot_h) * 2.5)
        a = int(245 * t)
        pygame.draw.rect(bot_grad, (10, 5, 0, a), (0, i, W, 1))

    pygame.event.clear()
    decision_made = False
    review_start  = time()

    while not decision_made:
        elapsed   = time() - review_start
        remaining = max(0.0, AUTO_SAVE - elapsed)

        # Photo plein écran
        screen.blit(photo_full, (0, 0))

        # Dégradés
        screen.blit(top_grad, (0, 0))
        screen.blit(bot_grad, (0, H - bot_h))

        # "Votre photo !" en haut
        titre = font_event.render("Votre photo !", True, (255, 243, 200))
        screen.blit(titre, (W // 2 - titre.get_width() // 2, int(top_h * 0.15)))

        # Barre de progression
        bar_y = H - bot_h + 4
        pygame.draw.rect(screen, (50, 28, 5),   (0, bar_y, W, 6))
        pygame.draw.rect(screen, (240, 195, 40), (0, bar_y, int(W * remaining / AUTO_SAVE), 6))

        # Countdown
        cd = font_confirmation.render(f"Sauvegarde automatique dans  {int(remaining)}s", True, (240, 195, 40))
        screen.blit(cd, (W // 2 - cd.get_width() // 2, H - bot_h + 16))

        # Boutons
        screen.blit(button_enregistrer, keep_rect.topleft)
        screen.blit(button_recommencer, retry_rect.topleft)

        pygame.display.flip()
        clock.tick(30)

        save_now = remaining <= 0
        retry_now = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if keep_rect.collidepoint(event.pos):
                    save_now = True
                elif retry_rect.collidepoint(event.pos):
                    retry_now = True

        if retry_now:
            os.remove(filepath)
            decision_made = True
            take_photo()
            return

        if save_now:
            decision_made = True
            photo_count += 1
            if user_settings.get("upload_auto", False):
                album_name = user_settings.get("event_name") or "Photobooth"
                threading.Thread(target=upload_in_background, args=(str(filepath), album_name), daemon=True).start()
            album_url = user_settings.get("cloud_path", "")
            qr_surf   = build_qr_surface(album_url)
            if qr_surf:
                show_qr_code(qr_surf, album_url)
            else:
                overlay = pygame.Surface(screen.get_size())
                overlay.set_alpha(180)
                overlay.fill((0, 0, 0))
                screen.blit(overlay, (0, 0))
                msg = font_confirmation.render("Photo enregistrée avec succès !", True, (255, 255, 255))
                screen.blit(msg, msg.get_rect(center=(W // 2, H // 2)))
                pygame.display.flip()
                pygame.time.wait(2000)


def draw_badge(text, font, x, y, align='left'):
    """Badge rétro cohérent avec le cadre : fond jaune doré, texte brun, coins arrondis."""
    surf = font.render(text, True, (55, 30, 5))
    px, py = 14, 6
    w, h = surf.get_width() + px * 2, surf.get_height() + py * 2
    if align == 'right':
        x = x - w
    bg = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(bg, (240, 195, 40, 210), (0, 0, w, h), border_radius=10)
    pygame.draw.rect(bg, (160, 110, 10, 240), (0, 0, w, h), width=2, border_radius=10)
    screen.blit(bg, (x, y))
    screen.blit(surf, (x + px, y + py))


def run_photobooth():
    running = True
    while running:
        vr = get_video_rect()
        W, H = screen.get_width(), screen.get_height()

        # A — Icône avec effet pulse (taille 150 ± 12px à ~2.5 Hz)
        pulse     = int(12 * math.sin(time() * 2.5))
        icon_size = 150 + pulse
        pulsed    = pygame.transform.smoothscale(icon_photo_base, (icon_size, icon_size))
        icon_rect = pulsed.get_rect(center=vr.center)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if not user_settings.get("kiosk_mode", False):
                        menu.run_config_menu(screen, user_settings)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if icon_rect.collidepoint(event.pos):
                    clicked = pygame.transform.smoothscale(icon_photo_base, (138, 138))
                    screen.blit(frame_overlay, (0, 0))
                    draw_video_frame()
                    screen.blit(clicked, clicked.get_rect(center=vr.center))
                    pygame.display.flip()
                    pygame.time.wait(100)
                    take_photo()

        # Ordre de rendu : cadre → caméra → UI
        screen.blit(frame_overlay, (0, 0))
        draw_video_frame()

        # D — Bordure dorée autour du preview
        pygame.draw.rect(screen, (200, 148, 18), vr.inflate(6, 6), width=3, border_radius=4)

        # A — Icône pulsée
        screen.blit(pulsed, icon_rect.topleft)

        # B — CTA plus grand, centré sous l'icône
        cta_surf = font_cta.render("Appuyez pour prendre la photo", True, (55, 30, 5))
        cta_w    = cta_surf.get_width() + 28
        cta_h    = cta_surf.get_height() + 12
        cta_x    = W // 2 - cta_w // 2
        cta_y    = icon_rect.bottom + 12
        cta_bg   = pygame.Surface((cta_w, cta_h), pygame.SRCALPHA)
        pygame.draw.rect(cta_bg, (240, 195, 40, 220), (0, 0, cta_w, cta_h), border_radius=10)
        pygame.draw.rect(cta_bg, (160, 110, 10, 240), (0, 0, cta_w, cta_h), width=2, border_radius=10)
        screen.blit(cta_bg, (cta_x, cta_y))
        screen.blit(cta_surf, (cta_x + 14, cta_y + 6))

        # C — Badge délai discret à droite du CTA
        delay_val = user_settings.get("delay", 3)
        draw_badge(f"⏱ {delay_val}s", font_caption, cta_x + cta_w + 10, cta_y + 4)

        # Nom de l'événement — centré dans la bande beige sous le preview
        event_name = user_settings.get("event_name", "")
        if event_name:
            beige_y = vr.bottom + int(H * 0.047)
            name_surf = font_event.render(event_name, True, (74, 42, 8))
            screen.blit(name_surf, (W // 2 - name_surf.get_width() // 2, beige_y - name_surf.get_height() // 2))

        # Compteur — petit badge coin haut-droit du preview
        label = f"{photo_count} photo{'s' if photo_count != 1 else ''} aujourd'hui"
        draw_badge(label, font_caption, vr.right - 8, vr.top + 8, align='right')

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    if not user_settings.get("autostart", False):
        menu.run_config_menu(screen, user_settings)
    run_photobooth()
