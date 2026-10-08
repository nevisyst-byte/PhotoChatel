import pygame
import os
import sys
import io
import threading
import subprocess
import shutil
import json
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

# === CHARTE UI ===
HEADER_H        = 90
HEADER_BG       = (255, 248, 231)
TITLE_COLOR     = (90, 50, 10)
SUBTITLE_COLOR  = (90, 50, 10)

VF_X, VF_Y     = 20, 90
VF_W, VF_H     = 984, 430
VF_BORDER       = (212, 160, 23)
VF_BORDER_W     = 4
DECO_Y          = 606

BTN_W, BTN_H        = 860, 80
BTN_Y               = 528
BTN_RADIUS          = 18
BTN_COLOR           = (212, 160, 23)
BTN_COLOR_HOV       = (184, 134, 11)
BTN_COLOR_PRE       = (160, 110,  5)
BTN_TEXT_COLOR      = (59, 31, 0)
BTN_BORDER_WIDTH    = 3

QR_HOME_SIZE    = 50
QR_HOME_POS     = (10, 708)
QR_RES_SIZE     = 220
QR_RES_POS      = (402, 280)

COUNTER_POS         = (512, 746)
COUNTER_COLOR       = (160, 140, 100)
COUNTER_FONT_SIZE   = 20

IDLE_TIMEOUT    = 45

RES_BG           = (255, 248, 231)
RES_TITLE_H      = 36
RES_FOOTER_H     = 110
RES_BORDER_COLOR = (212, 160, 23)
RES_BORDER_W     = 4
RES_PHOTO_MARGIN = 10

FONT_PATH_GREATVIBES = str(BASE_DIR / "assets" / "GreatVibes-Regular.ttf")

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
font_event_large   = pygame.font.Font(str(BASE_DIR / "assets" / "GreatVibes-Regular.ttf"), 58)
_title_size = 72
title_font = pygame.font.Font(str(BASE_DIR / "assets" / "fonts" / "Lobster-Regular.ttf"), _title_size)
while title_font.render("Châtel Rétromobile", True, (0, 0, 0)).get_width() > 1004:
    _title_size -= 4
    title_font = pygame.font.Font(str(BASE_DIR / "assets" / "fonts" / "Lobster-Regular.ttf"), _title_size)
font_subtitle      = pygame.font.SysFont(None, 26, bold=True)
font_idle_title    = pygame.font.Font(str(BASE_DIR / "assets" / "fonts" / "Lobster-Regular.ttf"), 52)
_idle_brand_size = 32
font_idle_brand  = pygame.font.Font(str(BASE_DIR / "assets" / "fonts" / "Lobster-Regular.ttf"), _idle_brand_size)
while font_idle_brand.render("Châtel Rétromobile", True, (0, 0, 0)).get_width() > 260:
    _idle_brand_size -= 2
    font_idle_brand = pygame.font.Font(str(BASE_DIR / "assets" / "fonts" / "Lobster-Regular.ttf"), _idle_brand_size)
font_idle_sub      = pygame.font.SysFont(None, 22)
font_idle_event    = pygame.font.SysFont(None, 18)
font_idle_date     = pygame.font.SysFont(None, 15)
font_res_title     = pygame.font.Font(str(BASE_DIR / "assets" / "fonts" / "Lobster-Regular.ttf"), 32)
font_res_timer     = pygame.font.Font(str(BASE_DIR / "assets" / "fonts" / "Lobster-Regular.ttf"), 48)
font_res_btn       = pygame.font.SysFont(None, 22)
font_res_tiny      = pygame.font.SysFont(None, 18)

# Police Unicode pour icônes boutons — avec fallback ASCII
_icon_font_names = ["dejavusans", "notosans", "freesans", "liberationsans"]
icon_font = None
for _name in _icon_font_names:
    _f = pygame.font.SysFont(_name, 22)
    if _f.render("📷", True, (0, 0, 0)).get_width() >= 8:
        icon_font = _f
        break
if icon_font is None:
    icon_font = pygame.font.SysFont(None, 22)
_icon_test = icon_font.render("📷", True, (0, 0, 0))
_retry_icon    = icon_font.render("\u21ba", True, (0, 0, 0))
BTN_ICON_RETRY = "\u21ba" if _retry_icon.get_width() >= 8 else ">>"
BTN_ICON_SAVE  = "✓"

user_settings = settings.load_settings()

# Brancher les paramètres configurables sur les constantes runtime
IDLE_TIMEOUT = int(user_settings.get("idle_timeout",   IDLE_TIMEOUT))

frame_overlay_raw = pygame.image.load(str(BASE_DIR / "assets" / "frame_retro.png"))
frame_overlay = pygame.transform.smoothscale(frame_overlay_raw.convert_alpha(), screen.get_size())

# Véhicules idle — subsurface de frame_overlay (remplacer par PNGs séparés si disponibles)
_sw, _sh = screen.get_width(), screen.get_height()
vehicle_images = [frame_overlay.subsurface(pygame.Rect(0, DECO_Y, _sw, _sh - DECO_Y))]
_max_veh_h = max(img.get_height() for img in vehicle_images)
IDLE_FOOTER_H  = max(110, min(160, _max_veh_h + 20))

icon_photo_base = pygame.image.load(str(BASE_DIR / "assets" / "icon_photo.png")).convert_alpha()
icon_photo = pygame.transform.scale(icon_photo_base, (150, 150))  # taille de base
button_enregistrer = pygame.image.load(str(BASE_DIR / "assets" / "button_enregistrer.png")).convert_alpha()
button_enregistrer = pygame.transform.smoothscale(button_enregistrer, (250, 90))
button_recommencer = pygame.image.load(str(BASE_DIR / "assets" / "button_recommencer.png")).convert_alpha()
button_recommencer = pygame.transform.smoothscale(button_recommencer, (250, 90))

base_save_path = BASE_DIR / "photos"
_today = datetime.now().strftime("%Y-%m-%d")
save_path = base_save_path / _today
os.makedirs(save_path, exist_ok=True)

photo_count = len([f for f in os.listdir(save_path) if f.endswith('.jpg')])

def get_daily_save_path():
    """Retourne le dossier du jour ; le crée et remet photo_count à zéro si minuit passé."""
    global save_path, photo_count
    folder = base_save_path / datetime.now().strftime("%Y-%m-%d")
    if folder != save_path:
        os.makedirs(folder, exist_ok=True)
        save_path   = folder
        photo_count = len([f for f in os.listdir(save_path) if f.endswith('.jpg')])
    return save_path

def find_usb_drive():
    """Détecte une clé USB montée sous /media/."""
    try:
        result = subprocess.run(
            ['lsblk', '-o', 'NAME,TYPE,MOUNTPOINT', '-J'],
            capture_output=True, text=True, timeout=5)
        data = json.loads(result.stdout)
        for device in data.get('blockdevices', []):
            for part in device.get('children', []):
                mp = part.get('mountpoint') or ''
                if '/media/' in mp:
                    return mp
    except Exception:
        pass
    media_path = '/media/chatel/'
    if os.path.exists(media_path):
        drives = [d for d in os.listdir(media_path)
                  if os.path.isdir(os.path.join(media_path, d))]
        if drives:
            return os.path.join(media_path, drives[0])
    return None


def copy_photos_to_usb():
    """Copie les photos du jour sur la clé USB détectée.
    Retourne (success: bool, message: str)."""
    usb_path = find_usb_drive()
    if not usb_path:
        return False, "Aucune clé USB détectée"
    try:
        date_str  = datetime.now().strftime("%Y-%m-%d")
        event     = user_settings.get("event_name", "Retromobile")
        dest      = os.path.join(usb_path, f"{event}_{date_str}")
        os.makedirs(dest, exist_ok=True)
        today     = datetime.now().strftime("%Y%m%d")
        src       = str(get_daily_save_path())
        photos    = [f for f in os.listdir(src)
                     if f.endswith('.jpg') and today in f]
        if not photos:
            photos = [f for f in os.listdir(src) if f.endswith('.jpg')]
        if not photos:
            return False, "Aucune photo à copier"
        for photo in photos:
            shutil.copy2(os.path.join(src, photo), os.path.join(dest, photo))
        return True, f"{len(photos)} photos copiées"
    except Exception as e:
        return False, str(e)


# QR code permanent affiché sur l'écran principal
qr_permanent = None  # initialisé après le chargement des settings

def refresh_qr_permanent():
    """Reconstruit le QR code permanent depuis les settings courants."""
    global qr_permanent
    url = user_settings.get("cloud_path", "")
    if not url or not url.startswith("http"):
        qr_permanent = None
        return
    try:
        qr = qrcode_lib.QRCode(box_size=4, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color=(55, 30, 5), back_color=(255, 248, 220))
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        surf = pygame.image.load(buf)
        qr_permanent = pygame.transform.scale(surf, (QR_HOME_SIZE, QR_HOME_SIZE))
    except Exception as e:
        print(f"QR permanent error: {e}")
        qr_permanent = None

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

refresh_qr_permanent()  # génère le QR au démarrage


def draw_header():
    W = screen.get_width()
    pygame.draw.rect(screen, HEADER_BG, (0, 0, W, HEADER_H))
    pygame.draw.line(screen, VF_BORDER, (0, HEADER_H), (W, HEADER_H), 2)
    title_surf = title_font.render("Châtel Rétromobile", True, TITLE_COLOR)
    real_h = title_surf.get_height()
    title_y = (HEADER_H // 2) - (real_h // 2) - 8
    screen.blit(title_surf, (W // 2 - title_surf.get_width() // 2, title_y))
    subtitle_text = user_settings.get("event_name", "")
    if subtitle_text:
        sub = font_subtitle.render(subtitle_text, True, SUBTITLE_COLOR)
        screen.blit(sub, (W // 2 - sub.get_width() // 2, 64))


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
    return pygame.Rect(VF_X, VF_Y, VF_W, VF_H)


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
    W, H = screen.get_width(), screen.get_height()
    cx, cy = W // 2, H // 2
    while current_count > 0:
        elapsed_total = time() - start_time
        new_count = delay - int(elapsed_total)
        if new_count != current_count:
            current_count = new_count

        # T7 — animation scale : 1.0 → 0.7 sur chaque seconde
        frac = elapsed_total - int(elapsed_total)
        scale_factor = max(0.7, 1.0 - 0.3 * frac)
        size = max(40, int(150 * scale_factor))
        font_dyn = pygame.font.Font(FONT_PATH_GREATVIBES, size)

        draw_video_frame(fullscreen=True)

        # Outline noir
        for dx, dy in [(-3, 0), (3, 0), (0, -3), (0, 3)]:
            s = font_dyn.render(str(current_count), True, (0, 0, 0))
            screen.blit(s, (cx - s.get_width() // 2 + dx, cy - s.get_height() // 2 + dy))
        # Texte blanc
        s = font_dyn.render(str(current_count), True, (255, 255, 255))
        screen.blit(s, (cx - s.get_width() // 2, cy - s.get_height() // 2))

        pygame.display.flip()
        clock.tick(30)


def show_qr_code(qr_surface, album_url):
    # T5 — QR grand centré sur l'écran résultat
    qr_big  = pygame.transform.scale(qr_surface, (QR_RES_SIZE, QR_RES_SIZE))
    qr_x, qr_y = QR_RES_POS
    W, H = screen.get_width(), screen.get_height()
    start = time()
    while time() - start < 6:
        screen.fill((10, 10, 10))
        screen.blit(qr_big, (qr_x, qr_y))

        msg1 = font_confirmation.render("Photo enregistrée !", True, (255, 255, 255))
        screen.blit(msg1, (W // 2 - msg1.get_width() // 2, qr_y - 60))

        lbl = font_label.render("Scannez pour récupérer votre photo !", True, (212, 160, 23))
        screen.blit(lbl, (W // 2 - lbl.get_width() // 2, qr_y + QR_RES_SIZE + 12))

        hint = font_label.render("Appuyez pour continuer", True, (100, 100, 100))
        screen.blit(hint, (W // 2 - hint.get_width() // 2, qr_y + QR_RES_SIZE + 36))

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
        img  = Image.open(str(filepath)).convert('RGBA')
        W, H = img.size
        try:
            font = PILFont.truetype(str(BASE_DIR / "assets" / "fonts" / "Lobster-Regular.ttf"), 18)
        except Exception:
            font = PILFont.load_default()
        bbox      = ImageDraw.Draw(img).textbbox((0, 0), text, font=font)
        tw, th    = bbox[2] - bbox[0], bbox[3] - bbox[1]
        pad_x, pad_y = 12, 5
        wm_w, wm_h   = tw + pad_x * 2, th + pad_y * 2

        # Calque RGBA transparent
        wm_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        wm_draw  = ImageDraw.Draw(wm_layer)

        wm_x = W - wm_w - 12
        wm_y = H - wm_h - 12

        # Fond noir semi-transparent
        wm_draw.rectangle([wm_x, wm_y, wm_x + wm_w, wm_y + wm_h],
                          fill=(0, 0, 0, 110))
        # Texte crème semi-transparent
        wm_draw.text((wm_x + pad_x, wm_y + pad_y), text,
                     fill=(255, 248, 231, 160), font=font)

        result = Image.alpha_composite(img, wm_layer)
        result.convert('RGB').save(str(filepath), quality=95)
    except Exception as e:
        print(f"Watermark error: {e}")


def focus_before_capture(timeout=2.5):
    """Mise au point automatique ponctuelle avant la photo.

    picam.configure() remet les contrôles à zéro : l'autofocus réglé au
    démarrage est donc perdu quand on passe en configuration "still".
    On relance une mise au point (AfMode Auto + AfTrigger Start) et on attend
    AfState = Focused (2) ou Failed (3). Retourne True si net, False sinon
    (la photo est alors prise quand même, avec la dernière position de l'objectif).
    """
    try:
        picam.set_controls({
            "AfMode": controls.AfModeEnum.Auto,
            "AfTrigger": controls.AfTriggerEnum.Start,
        })
        t0 = time()
        while time() - t0 < timeout:
            state = picam.capture_metadata().get("AfState")
            if state == 2:      # Focused
                return True
            if state == 3:      # Failed
                return False
        return False
    except Exception as e:
        print(f"Autofocus error: {e}")
        return False


def take_photo():
    global photo_count
    delay = int(user_settings.get("delay", 3))
    show_live_countdown(delay)

    # Geler la dernière frame caméra avant d'arrêter le preview
    frozen = pygame.surfarray.make_surface(yuv420_to_rgb(picam.capture_array("main")))
    frozen = pygame.transform.scale(frozen, screen.get_size())

    # Flash photo : pic blanc → fade sur la frame gelée (~90ms)
    flash_surf = pygame.Surface(screen.get_size())
    for alpha in (255, 200, 130, 70, 20, 0):
        screen.blit(frozen, (0, 0))
        flash_surf.fill((255, 255, 255))
        flash_surf.set_alpha(alpha)
        screen.blit(flash_surf, (0, 0))
        pygame.display.flip()
        pygame.time.wait(15)

    # Maintenir la frame gelée visible pendant la reconfiguration caméra
    screen.blit(frozen, (0, 0))
    pygame.display.flip()

    filename = datetime.now().strftime("photo_%Y%m%d_%H%M%S.jpg")
    filepath = get_daily_save_path() / filename

    picam.stop()
    capture_config = picam.create_still_configuration(main={"size": (1920, 1080)})
    picam.configure(capture_config)
    picam.set_controls({"AwbEnable": False, "ColourGains": gains})
    picam.start()
    focused = focus_before_capture()
    print(f"Autofocus avant capture : {'net' if focused else 'non confirmé'}")
    sleep(0.2)
    picam.capture_file(str(filepath))
    picam.stop()
    picam.configure(preview_config)
    picam.start()
    # configure() a remis les contrôles à zéro : on réactive l'autofocus continu
    picam.set_controls({"AfMode": 2, "AwbEnable": False, "ColourGains": gains})

    # D — Watermark
    add_watermark(filepath)

    try:
        photo_orig = pygame.image.load(str(filepath))
    except Exception:
        screen.fill((0, 0, 0))
        error_msg = font_confirmation.render("Erreur lors du chargement de la photo", True, (255, 0, 0))
        screen.blit(error_msg, (screen.get_width() // 2 - error_msg.get_width() // 2, 250))
        pygame.display.flip()
        pygame.time.wait(2000)
        return

    AUTO_SAVE     = int(user_settings.get("result_timeout", 9))
    W, H          = screen.get_width(), screen.get_height()
    qr_surf       = build_qr_surface(user_settings.get("cloud_path", ""))
    pygame.event.clear()
    review_start  = time()
    decision_made = False

    while not decision_made:
        elapsed   = time() - review_start
        remaining = max(0, int(AUTO_SAVE - elapsed))

        btn_retry, btn_save = draw_result_screen(photo_orig, remaining, qr_surf)
        pygame.display.flip()
        clock.tick(30)

        save_now  = remaining <= 0
        retry_now = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if btn_retry.collidepoint(event.pos):
                    retry_now = True
                elif btn_save.collidepoint(event.pos):
                    save_now = True

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
                threading.Thread(target=upload_in_background,
                                 args=(str(filepath), album_name), daemon=True).start()
            screen.fill((0, 0, 0))
            msg = font_confirmation.render("Photo enregistrée !", True, (255, 255, 255))
            screen.blit(msg, msg.get_rect(center=(W // 2, H // 2)))
            pygame.display.flip()
            pygame.time.wait(1200)


def draw_result_screen(photo_surf, remaining_secs, qr_surf):
    """Dessine l'écran résultat. Retourne (btn_retry_rect, btn_save_rect)."""
    W, H       = screen.get_width(), screen.get_height()
    footer_y   = H - RES_FOOTER_H
    photo_y    = HEADER_H + RES_TITLE_H
    photo_h    = footer_y - photo_y

    # ── Fond crème ────────────────────────────────────────────
    screen.fill(RES_BG)

    # ── Header identique à l'accueil ─────────────────────────
    draw_header()

    # ── Titre "Votre photo !" ─────────────────────────────────
    t_surf = font_res_title.render("Votre photo !", True, (90, 50, 10))
    screen.blit(t_surf, (
        (W - t_surf.get_width()) // 2,
        HEADER_H + (RES_TITLE_H - t_surf.get_height()) // 2))

    # ── Photo encadrée ────────────────────────────────────────
    frame_rect = pygame.Rect(
        RES_PHOTO_MARGIN,
        photo_y,
        W - RES_PHOTO_MARGIN * 2,
        photo_h - RES_PHOTO_MARGIN)
    inner_rect   = frame_rect.inflate(-RES_BORDER_W * 2, -RES_BORDER_W * 2)
    photo_scaled = pygame.transform.scale(photo_surf, (inner_rect.width, inner_rect.height))
    screen.blit(photo_scaled, inner_rect.topleft)
    pygame.draw.rect(screen, RES_BORDER_COLOR, frame_rect,
                     width=RES_BORDER_W, border_radius=10)

    # ── Barre basse ───────────────────────────────────────────
    pygame.draw.rect(screen, RES_BG, (0, footer_y, W, RES_FOOTER_H))
    pygame.draw.line(screen, RES_BORDER_COLOR, (0, footer_y), (W, footer_y), 4)

    footer_cy = footer_y + RES_FOOTER_H // 2

    # Colonne gauche — QR 80×80 + label
    QR_SIZE  = 80
    qr_x     = 16
    qr_y     = footer_y + (RES_FOOTER_H - QR_SIZE) // 2
    show_qr  = user_settings.get("show_qr", False)
    if show_qr and qr_surf:
        qr_small = pygame.transform.scale(qr_surf, (QR_SIZE, QR_SIZE))
        screen.blit(qr_small, (qr_x, qr_y))
        lbl = font_res_tiny.render("Scannez pour récupérer votre photo", True, (90, 50, 10))
        screen.blit(lbl, (qr_x + QR_SIZE + 8, footer_cy - lbl.get_height() // 2))
    else:
        msg_lines = ["Vos photos seront", "disponibles prochainement !"]
        for i, line in enumerate(msg_lines):
            s = font_res_tiny.render(line, True, (90, 50, 10))
            screen.blit(s, (qr_x, footer_cy - 14 + i * 22))

    # Colonne centre — chiffre countdown + libellés
    num_surf  = font_res_timer.render(str(remaining_secs), True, (212, 160, 23))
    lbl_top   = font_res_tiny.render("Sauvegarde dans", True, (139, 96, 48))
    lbl_bot   = font_res_tiny.render("secondes", True, (139, 96, 48))
    cx = W // 2
    screen.blit(lbl_top, (cx - lbl_top.get_width() // 2, footer_cy - 36))
    screen.blit(num_surf, (cx - num_surf.get_width() // 2, footer_cy - 20))
    screen.blit(lbl_bot,  (cx - lbl_bot.get_width() // 2,  footer_cy + 28))

    # Colonne droite — boutons 200×44
    BW, BH = 200, 44
    bx     = W - 16 - BW

    btn1_y    = footer_y + 10
    btn1_rect = pygame.Rect(bx, btn1_y, BW, BH)
    draw_btn_with_icon(btn1_rect,
                       icon_str=BTN_ICON_RETRY, label_str="Recommencer",
                       bg_color=(212, 160, 23), border_color=(139, 94, 0),
                       text_color=(59, 31, 0))

    btn2_y    = btn1_y + BH + 8
    btn2_rect = pygame.Rect(bx, btn2_y, BW, BH)
    draw_btn_with_icon(btn2_rect,
                       icon_str=BTN_ICON_SAVE, label_str="Enregistrer",
                       bg_color=(255, 248, 231), border_color=(212, 160, 23),
                       text_color=(90, 50, 10))

    return btn1_rect, btn2_rect  # recommencer, enregistrer


def draw_btn_with_icon(rect, icon_str, label_str,
                       bg_color, border_color, text_color):
    pygame.draw.rect(screen, bg_color,     rect, border_radius=12)
    pygame.draw.rect(screen, border_color, rect, width=2, border_radius=12)
    icon_surf  = icon_font.render(icon_str,  True, text_color)
    label_surf = font_res_btn.render(label_str, True, text_color)
    GAP     = 8
    total_w = icon_surf.get_width() + GAP + label_surf.get_width()
    start_x = rect.x + (rect.width - total_w) // 2
    cy      = rect.y + rect.height // 2
    screen.blit(icon_surf,  (start_x,
                              cy - icon_surf.get_height() // 2))
    screen.blit(label_surf, (start_x + icon_surf.get_width() + GAP,
                              cy - label_surf.get_height() // 2))


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


def draw_idle_screen():
    W, H     = screen.get_width(), screen.get_height()
    footer_y = H - IDLE_FOOTER_H
    cam_h    = footer_y

    # ── Zone caméra plein fond ────────────────────────────────
    try:
        yuv_frame = picam.capture_array("main")
        cam_surf  = pygame.surfarray.make_surface(yuv420_to_rgb(yuv_frame))
        cam_surf  = pygame.transform.scale(cam_surf, (W, cam_h))
        screen.blit(cam_surf, (0, 0))
    except Exception:
        screen.fill((0, 0, 0), (0, 0, W, cam_h))

    # ── Overlay central ───────────────────────────────────────
    OW, OH = 600, 130
    OX     = (W - OW) // 2
    OY     = (cam_h - OH) // 2

    ov = pygame.Surface((OW, OH), pygame.SRCALPHA)
    ov.fill((44, 26, 8, 185))
    screen.blit(ov, (OX, OY))

    pulse = abs(math.sin(time() * 1.5))
    pygame.draw.rect(screen, (212, 160, 23), (OX, OY, OW, OH),
                     width=2 + int(pulse * 2), border_radius=16)

    t_surf = font_idle_title.render("Prenez la pose !", True, (212, 160, 23))
    screen.blit(t_surf, (OX + (OW - t_surf.get_width()) // 2, OY + 8))

    s_surf = font_idle_sub.render("Appuyez sur le bouton pour votre photo", True, (255, 248, 231))
    screen.blit(s_surf, (OX + (OW - s_surf.get_width()) // 2,
                          OY + OH - s_surf.get_height() - 10))

    # ── Bande basse ───────────────────────────────────────────
    pygame.draw.rect(screen, (255, 248, 231), (0, footer_y, W, IDLE_FOOTER_H))
    pygame.draw.line(screen, (212, 160, 23), (0, footer_y), (W, footer_y), 4)

    # Véhicules — scalés pour tenir dans la bande, ancrés en bas
    target_h = IDLE_FOOTER_H - 20
    scaled_vehicles = []
    for img in vehicle_images:
        ratio = target_h / img.get_height()
        scaled_vehicles.append(
            pygame.transform.smoothscale(
                img, (int(img.get_width() * ratio), target_h)))

    gap     = 16
    total_w = sum(v.get_width() for v in scaled_vehicles) + gap * (len(scaled_vehicles) - 1)
    start_x = (W - total_w) // 2
    veh_y   = H - 10 - target_h
    offset  = 0
    for v in scaled_vehicles:
        screen.blit(v, (start_x + offset, veh_y))
        offset += v.get_width() + gap

    # Colonne gauche — brand sur 2 lignes, avant les véhicules
    left_col_w = start_x - 16
    line1 = font_idle_brand.render("Châtel",      True, (90, 50, 10))
    line2 = font_idle_brand.render("Rétromobile", True, (90, 50, 10))
    total_text_h = line1.get_height() + 6 + line2.get_height()
    line1_y = footer_y + (IDLE_FOOTER_H - total_text_h) // 2
    line2_y = line1_y + line1.get_height() + 6
    screen.blit(line1, ((left_col_w - line1.get_width()) // 2, line1_y))
    screen.blit(line2, ((left_col_w - line2.get_width()) // 2, line2_y))

    # Colonne droite — événement + date, aligné à droite
    event_text = user_settings.get("event_name", "")
    date_text  = datetime.now().strftime("%d/%m/%Y")
    right_x    = W - 16
    if event_text:
        ev_surf = font_idle_event.render(event_text, True, (90, 50, 10))
        ev_y    = footer_y + (IDLE_FOOTER_H // 2) - ev_surf.get_height() - 4
        screen.blit(ev_surf, (right_x - ev_surf.get_width(), ev_y))
    dt_surf = font_idle_date.render(date_text, True, (139, 96, 48))
    dt_y    = footer_y + (IDLE_FOOTER_H // 2) + 4
    screen.blit(dt_surf, (right_x - dt_surf.get_width(), dt_y))


def run_photobooth():
    running          = True
    last_interaction = time()
    font_counter_sm  = pygame.font.SysFont(None, COUNTER_FONT_SIZE)

    while running:
        vr = get_video_rect()
        W, H = screen.get_width(), screen.get_height()
        _cta_x = 75
        _cta_w = W - _cta_x * 2
        _cta_h = 62
        _cta_y = (VF_Y + VF_H) + (DECO_Y - (VF_Y + VF_H) - _cta_h) // 2
        btn_rect = pygame.Rect(_cta_x, _cta_y, _cta_w, _cta_h)

        is_idle = time() - last_interaction > IDLE_TIMEOUT

        # ── Événements ────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                last_interaction = time()
                if is_idle and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    take_photo()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                last_interaction = time()
                if is_idle:
                    # Flash bref sur l'overlay avant de basculer
                    OW, OH = 600, 130
                    OX = (W - OW) // 2
                    OY = ((H - IDLE_FOOTER_H) - OH) // 2
                    flash = pygame.Surface((OW, OH), pygame.SRCALPHA)
                    flash.fill((255, 255, 255, 80))
                    screen.blit(flash, (OX, OY))
                    pygame.display.flip()
                    pygame.time.wait(80)
                    take_photo()
                elif btn_rect.collidepoint(event.pos):
                    pygame.draw.rect(screen, BTN_COLOR_PRE, btn_rect, border_radius=BTN_RADIUS)
                    pygame.display.flip()
                    pygame.time.wait(80)
                    take_photo()

        # Écran idle
        if is_idle:
            draw_idle_screen()
            pygame.display.flip()
            clock.tick(30)
            continue

        # ── Rendu principal ───────────────────────────────────
        # T3 — Header code-based (remplace zone titre du PNG)
        draw_header()

        # Fond crème sous le header (aucune bande parasite)
        pygame.draw.rect(screen, HEADER_BG, (0, HEADER_H, W, H - HEADER_H))

        # Voitures du bas — blit sélectif du frame_retro.png
        screen.blit(frame_overlay, (0, 606), (0, 606, W, H - 606))
        # Bordure dorée zone véhicules — même épaisseur que le VF
        pygame.draw.rect(screen, VF_BORDER, pygame.Rect(0, 606, W, H - 606),
                         width=VF_BORDER_W, border_radius=4)

        # Caméra dans le VF
        draw_video_frame()

        # Bordure dorée VF
        pygame.draw.rect(screen, VF_BORDER, vr.inflate(VF_BORDER_W * 2, VF_BORDER_W * 2),
                         width=VF_BORDER_W, border_radius=4)

        # T4 — CTA button large
        mouse    = pygame.mouse.get_pos()
        is_hover = btn_rect.collidepoint(mouse)
        is_press = is_hover and pygame.mouse.get_pressed()[0]
        color    = BTN_COLOR_PRE if is_press else (BTN_COLOR_HOV if is_hover else BTN_COLOR)
        pygame.draw.rect(screen, color, btn_rect, border_radius=16)
        lbl = font_cta.render("Appuyez pour prendre la photo", True, BTN_TEXT_COLOR)
        screen.blit(lbl, (btn_rect.centerx - lbl.get_width() // 2,
                          btn_rect.centery - lbl.get_height() // 2))

        # T6 — Compteur pied d'écran
        cnt_txt = font_counter_sm.render(
            f"📷  {photo_count} photo{'s' if photo_count != 1 else ''} prise{'s' if photo_count != 1 else ''} aujourd'hui",
            True, COUNTER_COLOR)
        screen.blit(cnt_txt, (COUNTER_POS[0] - cnt_txt.get_width() // 2, COUNTER_POS[1]))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    if not user_settings.get("autostart", False):
        menu.run_config_menu(screen, user_settings, usb_copy_fn=copy_photos_to_usb)
        pygame.event.clear()   # vider le K_ESCAPE résiduel avant le photobooth
    run_photobooth()
