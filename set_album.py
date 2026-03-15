#!/usr/bin/env python3
"""
Utilisation :
  python3 set_album.py "https://photos.app.goo.gl/xxxx"
  python3 set_album.py "https://photos.app.goo.gl/xxxx" "Nom de l'événement"
"""
import sys
import settings

args = sys.argv[1:]

if not args:
    current = settings.load_settings()
    print(f"URL actuelle  : {current.get('cloud_path', '(vide)')}")
    print(f"Événement     : {current.get('event_name', '(vide)')}")
    print()
    print("Usage : python3 set_album.py \"<url>\" [\"<nom événement>\"]")
    sys.exit(0)

url = args[0]
s = settings.load_settings()
s["cloud_path"] = url

if len(args) >= 2:
    s["event_name"] = args[1]

settings.save_settings(s)
print(f"URL mise à jour  : {url}")
if len(args) >= 2:
    print(f"Événement        : {args[1]}")
