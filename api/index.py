from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import random
import yt_dlp

app = Flask(__name__)
CORS(app)

# 1. قائمة سيرفرات التحميل (للتحميل فقط)
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

# 2. دالة البحث (تستخدم yt-dlp محلياً لأنه آمن في البحث)
def search_yt(query):
    ydl_opts = {
        'default_search': 'ytsearch10',
        'quiet': True,
        'simulate': True,
        'extract_flat': True, # السر هنا: جلب العناوين فقط بدون تفاصيل ثقيلة
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            results = []
            for entry in info['entries']:
                if not entry: continue
                results.append({
                    'id': entry.get('id'),
                    'title': entry.get('title'),
                    'uploader': entry.get('uploader'),
                    'duration': entry.get('duration_string'),
                    'thumbnail': f"https://i.ytimg.com/vi/{entry.get('id')}/mqdefault.jpg",
                    'url': f"https://www.youtube.com/watch?v={entry.get('id')}"
                })
            return {'results': results}
    except Exception as e:
        return {'error': str(e)}

@app.route('/api/grab', methods=['POST', 'OPTIONS'])
def handler():
    if request.method == 'OPTIONS':
        return ('', 204, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        })

    data = request.json
    
    # أ) إذا كان طلب بحث
    if 'query' in data:
        return jsonify(search_yt(data['query']))

    # ب) إذا كان طلب تحميل
    url = data.get('url')
    if not url: return jsonify({'error': 'No URL provided'}), 400

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
            resp = requests.post(api_url, json=payload, headers=headers, timeout=8)
            if resp.status_code == 200:
                d = resp.json()
                if 'url' in d or 'picker' in d:
                    return jsonify({
                        'status': 'success',
                        'title': d.get('filename'),
                        'url': d.get('url'),
                        'picker': d.get('picker'),
                        'thumbnail': 'https://placehold.co/600x400/000/FFF?text=Video+Ready'
                    }), 200
        except:
            continue

    return jsonify({'error': 'فشلت جميع السيرفرات، يرجى المحاولة لاحقاً'}), 500
