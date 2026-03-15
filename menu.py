
import pygame
import settings

def run_config_menu(screen, user_settings):
    if not pygame.get_init():
        pygame.init()

    font       = pygame.font.SysFont(None, 26)
    font_title = pygame.font.SysFont(None, 32)
    clock      = pygame.time.Clock()

    W = screen.get_width()

    # Zones d'entrée (label au-dessus, champ en dessous)
    input_event = pygame.Rect(20, 70,  W - 40, 36)
    input_cloud = pygame.Rect(20, 150, W - 40, 36)
    input_delay = pygame.Rect(20, 230, 100,    36)

    # Valeurs initiales
    event_name  = user_settings.get("event_name", "")
    cloud_path  = user_settings.get("cloud_path", "")
    delay       = str(user_settings.get("delay", 3))
    autostart   = user_settings.get("autostart", False)
    upload_auto = user_settings.get("upload_auto", False)
    kiosk_mode  = user_settings.get("kiosk_mode", False)
    resolution  = user_settings.get("resolution", "FullHD")
    camera_mode = user_settings.get("camera_mode", "PiCam")

    color_inactive = pygame.Color('gray35')
    color_active   = pygame.Color('dodgerblue')
    active_field   = None

    CB_SIZE = 22
    checkbox_autostart = pygame.Rect(20, 290, CB_SIZE, CB_SIZE)
    checkbox_upload    = pygame.Rect(20, 330, CB_SIZE, CB_SIZE)
    checkbox_kiosk     = pygame.Rect(20, 370, CB_SIZE, CB_SIZE)

    resolution_options = ["HD", "FullHD", "4K"]
    camera_options     = ["PiCam", "USB"]
    resolution_index   = resolution_options.index(resolution) if resolution in resolution_options else 0
    camera_index       = camera_options.index(camera_mode)    if camera_mode    in camera_options    else 0

    btn_res = pygame.Rect(160, 415, 110, 30)
    btn_cam = pygame.Rect(160, 455, 110, 30)

    done = False
    while not done:
        screen.fill((18, 18, 18))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    done = True
                elif active_field == "event":
                    if   event.key == pygame.K_BACKSPACE: event_name = event_name[:-1]
                    elif event.key == pygame.K_RETURN:    active_field = None
                    else:                                  event_name += event.unicode
                elif active_field == "cloud":
                    if   event.key == pygame.K_BACKSPACE: cloud_path = cloud_path[:-1]
                    elif event.key == pygame.K_RETURN:    active_field = None
                    else:                                  cloud_path += event.unicode
                elif active_field == "delay":
                    if   event.key == pygame.K_BACKSPACE:                              delay = delay[:-1]
                    elif event.key == pygame.K_RETURN:                                 active_field = None
                    elif event.unicode.isdigit() and len(delay) < 2:                   delay += event.unicode
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if   input_event.collidepoint(pos):       active_field = "event"
                elif input_cloud.collidepoint(pos):       active_field = "cloud"
                elif input_delay.collidepoint(pos):       active_field = "delay"
                elif checkbox_autostart.collidepoint(pos): autostart   = not autostart
                elif checkbox_upload.collidepoint(pos):    upload_auto = not upload_auto
                elif checkbox_kiosk.collidepoint(pos):     kiosk_mode  = not kiosk_mode
                elif btn_res.collidepoint(pos):            resolution_index = (resolution_index + 1) % len(resolution_options)
                elif btn_cam.collidepoint(pos):            camera_index     = (camera_index     + 1) % len(camera_options)
                else:                                      active_field = None

        # ── Titre ──────────────────────────────────────────────
        screen.blit(font_title.render("Configuration du Photobooth", True, (255, 200, 50)), (20, 20))

        # ── Champs texte (label au-dessus) ─────────────────────
        def draw_field(label, rect, value, field_name):
            screen.blit(font.render(label, True, (170, 170, 170)), (rect.x, rect.y - 18))
            color = color_active if active_field == field_name else color_inactive
            pygame.draw.rect(screen, color, rect, 2)
            # Tronquer si texte trop long
            max_w = rect.width - 12
            txt_surf = font.render(value, True, (255, 255, 255))
            if txt_surf.get_width() > max_w:
                # Afficher la fin du texte
                clip = pygame.Surface((max_w, txt_surf.get_height()))
                clip.fill((18, 18, 18))
                clip.blit(txt_surf, (max_w - txt_surf.get_width(), 0))
                screen.blit(clip, (rect.x + 6, rect.y + 8))
            else:
                screen.blit(txt_surf, (rect.x + 6, rect.y + 8))

        draw_field("Nom de l'événement :", input_event, event_name, "event")
        draw_field("URL de l'album photo (QR code) :", input_cloud, cloud_path, "cloud")
        draw_field("Délai compte à rebours (secondes) :", input_delay, delay, "delay")

        # ── Checkboxes ─────────────────────────────────────────
        def draw_checkbox(rect, checked, label):
            pygame.draw.rect(screen, (200, 200, 200), rect)
            if checked:
                pygame.draw.line(screen, (0, 200, 80), rect.topleft, rect.bottomright, 3)
                pygame.draw.line(screen, (0, 200, 80), rect.topright, rect.bottomleft, 3)
            screen.blit(font.render(label, True, (230, 230, 230)), (rect.right + 10, rect.y + 2))

        draw_checkbox(checkbox_autostart, autostart,   "Démarrer automatiquement au boot")
        draw_checkbox(checkbox_upload,    upload_auto, "Upload automatique vers Google Photos")
        draw_checkbox(checkbox_kiosk,     kiosk_mode,  "Mode kiosque  (désactiver menu ESC)")

        # ── Dropdowns ──────────────────────────────────────────
        screen.blit(font.render("Résolution :", True, (170, 170, 170)), (20, 420))
        pygame.draw.rect(screen, (70, 70, 70), btn_res)
        screen.blit(font.render(resolution_options[resolution_index], True, (255, 255, 255)), (btn_res.x + 8, btn_res.y + 7))

        screen.blit(font.render("Caméra :", True, (170, 170, 170)), (20, 460))
        pygame.draw.rect(screen, (70, 70, 70), btn_cam)
        screen.blit(font.render(camera_options[camera_index], True, (255, 255, 255)), (btn_cam.x + 8, btn_cam.y + 7))

        # ── Instruction ────────────────────────────────────────
        screen.blit(font.render("Appuyez sur Échap pour sauvegarder et quitter", True, (100, 100, 100)), (20, 500))

        pygame.display.flip()
        clock.tick(30)

    # Sauvegarde
    user_settings["event_name"]  = event_name.strip()
    user_settings["cloud_path"]  = cloud_path.strip()
    user_settings["upload_auto"] = upload_auto
    user_settings["kiosk_mode"]  = kiosk_mode
    user_settings["autostart"]   = autostart
    user_settings["resolution"]  = resolution_options[resolution_index]
    user_settings["camera_mode"] = camera_options[camera_index]
    try:
        user_settings["delay"] = min(max(1, int(delay)), 10)
    except ValueError:
        user_settings["delay"] = 3
    settings.save_settings(user_settings)
