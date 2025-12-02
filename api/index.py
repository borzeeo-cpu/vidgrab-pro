from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import random

app = Flask(__name__)
CORS(app) # السماح للجميع بالاتصال

# قائمة الجيش: 22 سيرفر Cobalt لضمان عدم التوقف أبداً
COBALT_APIS = [
    "https://api.cobalt.tools/api/json",
    "https://cobalt.api.wuk.sh/api/json",
    "https://co.wuk.sh/api/json",
    "https://api.server.social/api/json",
    "https://cobalt.deno.dev/api/json",
    "https://c1.saveweb.org/api/json",
    "https://cobalt.saveweb.org/api/json",
    "https://cobalt.tools2.net/api/json",
    "https://co2.saveweb.org/api/json",
    "https://api.y2dl.org/api/json",
    "https://cobalt.saveporn.net/api/json",
    "https://cobalt.fastvps.eu.org/api/json",
    "https://cobalt.vern.cc/api/json",
    "https://cobalt.up.railway.app/api/json",
    "https://cobalt.booz.in/api/json",
    "https://api.cobalt.pm/api/json",
    "https://cobalt.drgns.space/api/json",
    "https://cobalt.nvme0n1p2.sh/api/json",
    "https://cobalt.sefod.eu.org/api/json",
    "https://cobalt.reichis.tech/api/json",
    "https://cobalt.aprxl.com/api/json",
    "https://cobalt.tokamak.workers.dev/api/json"
]

@app.route('/api/grab', methods=['POST', 'OPTIONS'])
def grab_video():
    # إعدادات CORS
    if request.method == 'OPTIONS':
        return ('', 204, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        })

    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    # خلط السيرفرات عشوائياً لتوزيع الحمل
    random.shuffle(COBALT_APIS)

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "VidGrab/Pro"
    }

    payload = {
        "url": url,
        "videoQuality": "max",
        "filenamePattern": "basic",
        "tiktokH265": False,
        "twitterGif": True,
        "youtubeVideoCodec": "h264"
    }

    # تجربة السيرفرات واحداً تلو الآخر
    for api_url in COBALT_APIS:
        try:
            # مهلة 6 ثواني لكل سيرفر لسرعة التنقل
            resp = requests.post(api_url, json=payload, headers=headers, timeout=6)
            
            if resp.status_code == 200:
                data = resp.json()
                
                # التأكد أن الرد سليم
                if 'url' in data or 'picker' in data:
                    return jsonify({
                        'status': 'success',
                        'title': data.get('filename', 'Video Download'),
                        'url': data.get('url'),
                        'picker': data.get('picker'),
                        'thumbnail': 'https://placehold.co/600x400/000/FFF?text=Video+Ready',
                        'server_used': api_url # لنعرف أي سيرفر نجح (للمطور فقط)
                    }), 200
        except Exception:
            continue # السيرفر فشل؟ جرب اللي بعده فوراً

    return jsonify({'error': 'فشلت جميع السيرفرات، يرجى المحاولة لاحقاً.'}), 500

# هذا السطر مهم لتشغيل Flask على Vercel
app.debug = True
