#!/bin/bash
cd ~/marmara_weather || exit 1
git add .
git commit -m "Site guncellemesi: $(date '+%Y-%m-%d %H:%M')" || exit 0
git push origin main

curl -s -X POST "https://api.vercel.com/v1/integrations/deploy/prj_w1G9OkOjdRHktLo25UTnPDxaeKVL/Q32i4r5Nje" > /dev/null
