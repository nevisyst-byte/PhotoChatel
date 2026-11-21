
import pygame
import settings


def run_config_menu(screen, user_settings, usb_copy_fn=None):
    if not pygame.get_init():
        pygame.init()

    font       = pygame.font.SysFont(None, 26)
    font_title = pygame.font.SysFont(None, 32)
    font_msg   = pygame.font.SysFont(None, 24)
    clock      = pygame.time.Clock()

    W = screen.get_width()

    # ── Champs texte / numériques ──────────────────────────────
    input_event   = pygame.Rect(20,  50, W - 40, 36)
    input_cloud   = pygame.Rect(20, 105, W - 40, 36)
    input_delay   = pygame.Rect(20, 160, 100,    36)
    input_idle    = pygame.Rect(20, 210, 100,    36)
    input_result  = pygame.Rect(20, 255, 100,    36)
    input_folder  = pygame.Rect(20, 305, W - 40, 36)

    # ── Valeurs initiales ─────────────────────────────────────
    event_name     = user_settings.get("event_name",     "")
    cloud_path     = user_settings.get("cloud_path",     "")
    delay          = str(user_settings.get("delay",           3))
    idle_timeout   = str(user_settings.get("idle_timeout",   45))
    result_timeout = str(user_settings.get("result_timeout", 10))
    save_folder    = user_settings.get("save_folder",    "~/Photos")
    autostart      = user_settings.get("autostart",      False)
    upload_auto    = user_settings.get("upload_auto",    False)
    kiosk_mode     = user_settings.get("kiosk_mode",     False)
    show_qr        = user_settings.get("show_qr",        False)
    resolution     = user_settings.get("resolution",     "FullHD")
    camera_mode    = user_settings.get("camera_mode",    "PiCam")

    ev_options = [-2.0, -1.0, 0.0, 1.0, 2.0]
    try:
        ev_index = ev_options.index(float(user_settings.get("camera_ev", 0.0)))
    except ValueError:
        ev_index = 2

    color_inactive = pygame.Color('gray35')
    color_active   = pygame.Color('dodgerblue')
    active_field   = None

    CB_SIZE = 22
    checkbox_autostart = pygame.Rect(20, 395, CB_SIZE, CB_SIZE)
    checkbox_upload    = pygame.Rect(20, 428, CB_SIZE, CB_SIZE)
    checkbox_kiosk     = pygame.Rect(20, 461, CB_SIZE, CB_SIZE)
    checkbox_show_qr   = pygame.Rect(20, 494, CB_SIZE, CB_SIZE)

    resolution_options = ["HD", "FullHD", "4K"]
    camera_options     = ["PiCam", "USB"]
    resolution_index   = resolution_options.index(resolution) if resolution in resolution_options else 1
    camera_index       = camera_options.index(camera_mode)    if camera_mode    in camera_options    else 0

    btn_ev    = pygame.Rect(230, 353, 130,  30)
    btn_res   = pygame.Rect(230, 530, 110,  30)
    btn_cam   = pygame.Rect(230, 566, 110,  30)
    btn_reset = pygame.Rect( 20, 603, 260,  34)
    btn_usb   = pygame.Rect(300, 603, 260,  34)

    status_msg  = ""   # message affiché après action bouton
    status_until = 0   # timestamp fin d'affichage

    def show_status(text):
        nonlocal status_msg, status_until
        status_msg   = text
        status_until = pygame.time.get_ticks() + 3000

    done = False
    while not done:
        now_ticks = pygame.time.get_ticks()
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
                elif active_field == "folder":
                    if   event.key == pygame.K_BACKSPACE: save_folder = save_folder[:-1]
                    elif event.key == pygame.K_RETURN:    active_field = None
                    else:                                  save_folder += event.unicode
                elif active_field == "delay":
                    if   event.key == pygame.K_BACKSPACE:                       delay = delay[:-1]
                    elif event.key == pygame.K_RETURN:                          active_field = None
                    elif event.unicode.isdigit() and len(delay) < 2:            delay += event.unicode
                elif active_field == "idle":
                    if   event.key == pygame.K_BACKSPACE:                       idle_timeout = idle_timeout[:-1]
                    elif event.key == pygame.K_RETURN:                          active_field = None
                    elif event.unicode.isdigit() and len(idle_timeout) < 3:     idle_timeout += event.unicode
                elif active_field == "result":
                    if   event.key == pygame.K_BACKSPACE:                       result_timeout = result_timeout[:-1]
                    elif event.key == pygame.K_RETURN:                          active_field = None
                    elif event.unicode.isdigit() and len(result_timeout) < 2:   result_timeout += event.unicode

            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if   input_event.collidepoint(pos):          active_field = "event"
                elif input_cloud.collidepoint(pos):          active_field = "cloud"
                elif input_delay.collidepoint(pos):          active_field = "delay"
                elif input_idle.collidepoint(pos):           active_field = "idle"
                elif input_result.collidepoint(pos):         active_field = "result"
                elif input_folder.collidepoint(pos):         active_field = "folder"
                elif checkbox_autostart.collidepoint(pos):   autostart   = not autostart
                elif checkbox_upload.collidepoint(pos):      upload_auto = not upload_auto
                elif checkbox_kiosk.collidepoint(pos):       kiosk_mode  = not kiosk_mode
                elif checkbox_show_qr.collidepoint(pos):     show_qr     = not show_qr
                elif btn_ev.collidepoint(pos):               ev_index    = (ev_index + 1) % len(ev_options)
                elif btn_res.collidepoint(pos):              resolution_index = (resolution_index + 1) % len(resolution_options)
                elif btn_cam.collidepoint(pos):              camera_index     = (camera_index     + 1) % len(camera_options)
                elif btn_reset.collidepoint(pos):
                    user_settings["reset_counter"] = True
                    settings.save_settings(user_settings)
                    show_status("Compteur remis à zéro")
                elif btn_usb.collidepoint(pos):
                    if usb_copy_fn:
                        show_status("Copie en cours...")
                        screen.fill((18, 18, 18))
                        pygame.display.flip()
                        ok, msg = usb_copy_fn()
                        show_status(("✓ " if ok else "✗ ") + msg)
                    else:
                        show_status("Fonction USB non disponible")
                else:
                    active_field = None

        # ── Titre ──────────────────────────────────────────────
        screen.blit(font_title.render("Configuration du Photobooth", True, (255, 200, 50)), (20, 15))

        # ── Helper champ texte ─────────────────────────────────
        def draw_field(label, rect, value, field_name):
            screen.blit(font.render(label, True, (170, 170, 170)), (rect.x, rect.y - 18))
            color = color_active if active_field == field_name else color_inactive
            pygame.draw.rect(screen, color, rect, 2)
            max_w    = rect.width - 12
            txt_surf = font.render(value, True, (255, 255, 255))
            if txt_surf.get_width() > max_w:
                clip = pygame.Surface((max_w, txt_surf.get_height()))
                clip.fill((18, 18, 18))
                clip.blit(txt_surf, (max_w - txt_surf.get_width(), 0))
                screen.blit(clip, (rect.x + 6, rect.y + 8))
            else:
                screen.blit(txt_surf, (rect.x + 6, rect.y + 8))

        draw_field("Nom de l'événement :",                  input_event,  event_name,     "event")
        draw_field("URL de l'album photo (QR code) :",      input_cloud,  cloud_path,     "cloud")
        draw_field("Délai compte à rebours (secondes) :",   input_delay,  delay,          "delay")
        draw_field("Délai avant veille (secondes) :",       input_idle,   idle_timeout,   "idle")
        draw_field("Durée affichage résultat (secondes) :", input_result, result_timeout, "result")
        draw_field("Dossier photos :",                      input_folder, save_folder,    "folder")

        # ── Exposition caméra ──────────────────────────────────
        screen.blit(font.render("Exposition caméra (EV) :", True, (170, 170, 170)), (20, 358))
        pygame.draw.rect(screen, (70, 70, 70), btn_ev)
        screen.blit(font.render(f"{ev_options[ev_index]:+.1f} EV", True, (255, 255, 255)),
                    (btn_ev.x + 8, btn_ev.y + 7))

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
        draw_checkbox(checkbox_show_qr,   show_qr,     "Afficher QR code (album en ligne disponible)")

        # ── Dropdowns résolution / caméra ──────────────────────
        screen.blit(font.render("Résolution :", True, (170, 170, 170)), (20, 535))
        pygame.draw.rect(screen, (70, 70, 70), btn_res)
        screen.blit(font.render(resolution_options[resolution_index], True, (255, 255, 255)),
                    (btn_res.x + 8, btn_res.y + 7))

        screen.blit(font.render("Caméra :", True, (170, 170, 170)), (20, 571))
        pygame.draw.rect(screen, (70, 70, 70), btn_cam)
        screen.blit(font.render(camera_options[camera_index], True, (255, 255, 255)),
                    (btn_cam.x + 8, btn_cam.y + 7))

        # ── Bouton reset compteur ──────────────────────────────
        pygame.draw.rect(screen, (90, 30, 30), btn_reset, border_radius=6)
        pygame.draw.rect(screen, (180, 60, 60), btn_reset, width=2, border_radius=6)
        lbl_r = font.render("Remettre compteur à zéro", True, (255, 180, 180))
        screen.blit(lbl_r, (btn_reset.x + (btn_reset.width  - lbl_r.get_width())  // 2,
                             btn_reset.y + (btn_reset.height - lbl_r.get_height()) // 2))

        # ── Bouton copie USB ───────────────────────────────────
        pygame.draw.rect(screen, (30, 80, 160), btn_usb, border_radius=6)
        pygame.draw.rect(screen, (80, 140, 220), btn_usb, width=2, border_radius=6)
        lbl_u = font.render("Copier photos sur clé USB", True, (255, 255, 255))
        screen.blit(lbl_u, (btn_usb.x + (btn_usb.width  - lbl_u.get_width())  // 2,
                             btn_usb.y + (btn_usb.height - lbl_u.get_height()) // 2))

        # ── Message de statut (3s) ─────────────────────────────
        if status_msg and now_ticks < status_until:
            ov = pygame.Surface((W - 40, 36), pygame.SRCALPHA)
            ov.fill((44, 26, 8, 220))
            screen.blit(ov, (20, 648))
            s = font_msg.render(status_msg, True, (255, 248, 231))
            screen.blit(s, (20 + (W - 40 - s.get_width()) // 2, 655))

        # ── Instruction ────────────────────────────────────────
        screen.blit(font.render("Appuyez sur Échap pour sauvegarder et quitter",
                                True, (100, 100, 100)), (20, 695))

        pygame.display.flip()
        clock.tick(30)

    # ── Sauvegarde ─────────────────────────────────────────────
    user_settings["event_name"]  = event_name.strip()
    user_settings["cloud_path"]  = cloud_path.strip()
    user_settings["upload_auto"] = upload_auto
    user_settings["kiosk_mode"]  = kiosk_mode
    user_settings["autostart"]   = autostart
    user_settings["show_qr"]     = show_qr
    user_settings["resolution"]  = resolution_options[resolution_index]
    user_settings["camera_mode"] = camera_options[camera_index]
    user_settings["save_folder"] = save_folder.strip()
    user_settings["camera_ev"]   = ev_options[ev_index]
    try:
        user_settings["delay"]          = min(max(1,  int(delay)),          10)
        user_settings["idle_timeout"]   = min(max(10, int(idle_timeout)),  120)
        user_settings["result_timeout"] = min(max(5,  int(result_timeout)), 30)
    except ValueError:
        user_settings["delay"]          = user_settings.get("delay",          3)
        user_settings["idle_timeout"]   = user_settings.get("idle_timeout",  45)
        user_settings["result_timeout"] = user_settings.get("result_timeout", 10)
    settings.save_settings(user_settings)
