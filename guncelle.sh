#!/bin/bash
cd ~/marmara_weather || exit 1
git add .
git commit -m "Site guncellemesi: $(date '+%Y-%m-%d %H:%M')" || exit 0
git push origin main
