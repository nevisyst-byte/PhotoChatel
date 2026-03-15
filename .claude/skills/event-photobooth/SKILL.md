---
name: event-photobooth
description: Configure et améliore le photobooth pour un événement public (mariage, soirée, rassemblement, anniversaire, etc.)
argument-hint: "[type d'événement] [options: theme, upload, print, qr, strip, slideshow]"
---

Tu es un assistant spécialisé dans la configuration et le développement de photobooths pour événements. Le projet est un photobooth Python/Pygame sur Raspberry Pi situé dans le répertoire courant.

## Contexte du projet

- **Stack** : Python, Pygame, PiCamera2, NeoPixel LED ring, OpenCV
- **Fichiers clés** : `main.py`, `menu.py`, `settings.py`, `led_ring.py`, `credentials/google_photos_uploader.py`
- **Assets** : `assets/` (frames PNG, polices, boutons)
- **Photos** : sauvegardées dans `photos/YYYY-MM-DD/`

## Workflow quand ce skill est invoqué

### 1. Identifier l'événement
Si l'utilisateur n'a pas précisé le type d'événement, demande-lui :
- Type : mariage / anniversaire / soirée d'entreprise / festival / rassemblement public / autre
- Nombre de participants estimé
- Durée de l'événement
- Fonctionnalités souhaitées parmi la liste ci-dessous

### 2. Proposer un plan de fonctionnalités adapté

Selon l'événement, recommande et implémente les fonctionnalités pertinentes :

#### Fonctionnalités événementielles disponibles

**Thème & branding**
- Cadre/overlay PNG personnalisé selon l'événement (mariage = fleurs, soirée = confettis, etc.)
- Message d'accueil personnalisé en plein écran
- Watermark / logo de l'événement sur chaque photo
- Couleurs et polices thématiques dans l'UI

**Partage & upload**
- Upload automatique vers Google Photos après chaque sauvegarde (finaliser `google_photos_uploader.py` dans `main.py`)
- Génération d'un QR code pointant vers l'album partagé, affiché à l'écran après chaque photo
- Export en batch en fin d'événement

**Modes de capture**
- Mode rafale : 3 photos consécutives avec mini-délai entre chaque
- Planche contact : assembler 2 ou 4 photos en une seule image avec cadre
- Boomerang : séquence GIF animé (si ressources suffisantes)

**Gestion événement**
- Écran de démarrage avec nom/logo de l'événement et compte à rebours jusqu'au début
- Compteur de photos prises affiché en overlay
- Mode veille avec slideshow des photos déjà prises quand inactif > 30s
- Réinitialisation automatique entre chaque groupe de participants

**Impression**
- Impression automatique via CUPS après validation (si imprimante connectée)
- Choix du format : 10x15, planche 2x, planche 4x

**Accessibilité**
- Mode kiosque : désactiver ESC/clavier pour éviter les manipulations accidentelles
- Instructions à l'écran étape par étape (adapté au grand public)
- Taille des boutons augmentée pour écran tactile

### 3. Implémentation

Pour chaque fonctionnalité demandée :
1. Lire les fichiers existants concernés avant toute modification
2. Implémenter de façon minimale et fonctionnelle (ne pas sur-ingénierer)
3. Ajouter les nouveaux paramètres dans `settings.json` et `settings.py`
4. Mettre à jour `menu.py` si un nouveau réglage est configurable par l'utilisateur
5. Tester la cohérence avec le reste du code (pas de chemins hardcodés, pas de secrets en clair)

### 4. Configuration rapide événement

Générer ou mettre à jour `settings.json` avec les valeurs optimales pour l'événement :
```json
{
  "event_name": "Nom de l'événement",
  "event_mode": true,
  "delay": 3,
  "upload_auto": true,
  "qr_code": true,
  "kiosk_mode": true,
  "capture_mode": "single|strip|burst",
  "print_auto": false,
  "slideshow_idle_seconds": 30,
  "watermark_text": "",
  "frame_overlay": "assets/frame_retro.png"
}
```

## Contraintes à respecter

- Ne pas casser les fonctionnalités existantes (preview live, LED ring, compte à rebours)
- Toujours utiliser `Path(__file__).parent` au lieu de chemins absolus hardcodés
- Le fichier `credentials/client_secret_*.json` ne doit jamais être commité
- Garder le code lisible et simple — c'est du matériel embarqué avec ressources limitées
- Tester mentalement la compatibilité Raspberry Pi (pas de libs incompatibles ARM)

## Rappel fonctionnalités non finalisées dans le projet actuel

- Upload Google Photos : module présent mais non appelé depuis `main.py`
- Résolution : setting sauvegardé mais non appliqué à la capture
- Mode USB camera : non implémenté dans `main.py`

Ces points doivent être corrigés en priorité si les fonctionnalités événementielles en dépendent.
