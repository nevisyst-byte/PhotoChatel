# Plan UI Refactor — Châtel Rétromobile Photobooth
**Date :** 2026-03-29
**Objectif :** Refondre l'IHM de main.py selon la nouvelle charte visuelle (1024×768)

---

## Architecture

Tout le code UI est dans `main.py` (module unique, ~500 lignes).
Aucun autre fichier UI à modifier sauf `main.py`.

### Décision structurelle importante
La `frame_retro.png` est actuellement le fond principal (titre + cadre + voitures).
Le nouveau layout place le VF à y=95 (DANS la zone titre du PNG).
→ **Le PNG sera conservé uniquement pour les voitures du bas (y=552→720).**
→ Un header code-based (90px) remplace la zone titre du PNG.
→ Le VF élargi (984×400) couvre le fond marron du PNG.

---

## Fichiers modifiés

| Fichier | Changement |
|---------|-----------|
| `main.py` | Refonte UI complète — constantes, layout, CTA, VF, header, QR, idle |

---

## Tâches

### T1 — Bloc constantes "=== CHARTE UI ===" (2 min)
**Fichier :** `main.py` (en tête, après les imports)

Remplacer les valeurs dispersées par un bloc de constantes nommées :
```python
# === CHARTE UI ===
HEADER_H        = 90
HEADER_BG       = (255, 248, 231)
TITLE_COLOR     = (90, 50, 10)
SUBTITLE_COLOR  = (140, 80, 20)

VF_X, VF_Y     = 20, 95
VF_W, VF_H     = 984, 400
VF_BORDER       = (212, 160, 23)
VF_BORDER_W     = 4

BTN_W, BTN_H   = 860, 100
BTN_Y          = 520
BTN_RADIUS     = 18
BTN_COLOR      = (212, 160, 23)
BTN_COLOR_HOV  = (184, 134, 11)
BTN_COLOR_PRE  = (160, 110, 5)
BTN_TEXT_COLOR = (59, 31, 0)

QR_HOME_SIZE   = 50
QR_HOME_POS    = (10, 708)
QR_RES_SIZE    = 220
QR_RES_POS     = (402, 280)

COUNTER_POS    = (512, 755)
COUNTER_COLOR  = (160, 140, 100)

IDLE_TIMEOUT   = 45
SLIDE_INTERVAL = 4
```
**Critère :** constantes accessibles globalement, aucune valeur magique dans le code

---

### T2 — Réécrire `get_video_rect()` (2 min)
**Fichier :** `main.py`

```python
def get_video_rect():
    return pygame.Rect(VF_X, VF_Y, VF_W, VF_H)
```
**Impact :** VF passe de 877×330@(79,222) à 984×400@(20,95)
**Critère :** toutes les fonctions qui appellent `get_video_rect()` s'adaptent automatiquement

---

### T3 — Nouvelle fonction `draw_header()` (3 min)
**Fichier :** `main.py`

```python
def draw_header():
    W = screen.get_width()
    pygame.draw.rect(screen, HEADER_BG, (0, 0, W, HEADER_H))
    pygame.draw.line(screen, VF_BORDER, (0, HEADER_H), (W, HEADER_H), 2)
    title = font_event_large.render("Châtel Rétromobile", True, TITLE_COLOR)
    subtitle_text = user_settings.get("event_name", "")
    if subtitle_text:
        sub = font_caption.render(subtitle_text, True, SUBTITLE_COLOR)
        # Titre centré verticalement dans la moitié haute
        screen.blit(title, (W//2 - title.get_width()//2, 8))
        screen.blit(sub,   (W//2 - sub.get_width()//2,   HEADER_H - sub.get_height() - 8))
    else:
        screen.blit(title, (W//2 - title.get_width()//2, HEADER_H//2 - title.get_height()//2))
```
**Critère :** header visible, titre + sous-titre si event_name défini

---

### T4 — Nouveau CTA button large (4 min)
**Fichier :** `main.py` — dans `run_photobooth()`

Remplacer l'icône pulsée + badge "Appuyez..." par :
```python
BTN_X_CALC = (W - BTN_W) // 2

# État visuel
mouse     = pygame.mouse.get_pos()
btn_rect  = pygame.Rect(BTN_X_CALC, BTN_Y, BTN_W, BTN_H)
is_hover  = btn_rect.collidepoint(mouse)
is_press  = is_hover and pygame.mouse.get_pressed()[0]
color     = BTN_COLOR_PRE if is_press else (BTN_COLOR_HOV if is_hover else BTN_COLOR)

pygame.draw.rect(screen, color, btn_rect, border_radius=BTN_RADIUS)
pygame.draw.rect(screen, BTN_TEXT_COLOR, btn_rect, width=BTN_BORDER_WIDTH, border_radius=BTN_RADIUS)
lbl = font_cta.render("Appuyez pour prendre la photo", True, BTN_TEXT_COLOR)
screen.blit(lbl, (btn_rect.centerx - lbl.get_width()//2,
                  btn_rect.centery - lbl.get_height()//2))
```
Clic détecté sur `btn_rect` → déclenche `take_photo()`
**Critère :** bouton doré 860px visible, 3 états visuels fonctionnels

---

### T5 — QR code conditionnel (3 min)
**Fichier :** `main.py`

- Écran accueil : générer `qr_permanent` à QR_HOME_SIZE=50 (box_size=2)
- L'afficher à QR_HOME_POS=(10, 708), discret, sans label
- Écran résultat : utiliser QR_RES_SIZE=220, centré à QR_RES_POS=(402, 280)
  avec label "Scannez pour récupérer votre photo !"

---

### T6 — Compteur en pied d'écran (2 min)
**Fichier :** `main.py` — dans `run_photobooth()`

Remplacer le badge compteur en haut-droit du VF par :
```python
font_counter_small = pygame.font.SysFont(None, COUNTER_FONT_SIZE)  # 14px
txt = font_counter_small.render(f"📷  {photo_count} photos prises aujourd'hui", True, COUNTER_COLOR)
screen.blit(txt, (COUNTER_POS[0] - txt.get_width()//2, COUNTER_POS[1]))
```
**Critère :** compteur en bas, discret, non-intrusif

---

### T7 — Countdown amélioré avec animation scale (4 min)
**Fichier :** `main.py` — `show_live_countdown()`

Pendant le décompte (3, 2, 1) :
- Chiffre centré sur le VF fullscreen
- Scale animée : `scale = 1.0 - 0.3 * frac_elapsed_in_second` (1.0 → 0.7)
- Outline noir 3px : render text noir décalé ±3px avant le blanc
```python
scale_factor = max(0.7, 1.0 - 0.3 * (elapsed_frac % 1.0))
size = int(150 * scale_factor)
font_dyn = pygame.font.Font(FONT_PATH_GREATVIBES, size)
# outline
for dx, dy in [(-3,0),(3,0),(0,-3),(0,3)]:
    s = font_dyn.render(str(current_count), True, (0,0,0))
    screen.blit(s, (cx - s.get_width()//2 + dx, cy - s.get_height()//2 + dy))
# texte principal
s = font_dyn.render(str(current_count), True, (255,255,255))
screen.blit(s, (cx - s.get_width()//2, cy - s.get_height()//2))
```
**Critère :** animation fluide, chiffre lisible avec outline

---

### T8 — Écran idle / slideshow (5 min)
**Fichier :** `main.py` — dans `run_photobooth()`

```python
last_interaction = time()
slide_photos = []
slide_idx = 0
slide_last = 0

# En haut de la boucle while :
if time() - last_interaction > IDLE_TIMEOUT:
    # Charger les photos du jour si nécessaire
    if not slide_photos:
        slide_photos = sorted(save_path.glob("*.jpg"))
    if slide_photos:
        now = time()
        if now - slide_last > SLIDE_INTERVAL:
            slide_idx = (slide_idx + 1) % len(slide_photos)
            slide_last = now
        img = pygame.image.load(str(slide_photos[slide_idx]))
        img = pygame.transform.smoothscale(img, screen.get_size())
        screen.blit(img, (0,0))
        # Overlay semi-transparent
        ov = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 140))
        screen.blit(ov, (0,0))
        msg = font_cta.render("Appuyez pour prendre votre photo !", True, (255,248,200))
        screen.blit(msg, (W//2 - msg.get_width()//2, H//2 - msg.get_height()//2))
        pygame.display.flip(); clock.tick(30); continue

# Toute interaction remet le compteur
last_interaction = time()  # dans les handlers MOUSEBUTTONDOWN et KEYDOWN
```
**Critère :** après 45s, slideshow des photos du jour avec overlay CTA

---

## Ordre d'exécution recommandé
T1 → T2 → T3 → T4 → T5 → T6 → T7 → T8

## Risque principal
T2 change les dimensions du VF — vérifier que `show_live_countdown()` et `take_photo()` fonctionnent toujours correctement après.
