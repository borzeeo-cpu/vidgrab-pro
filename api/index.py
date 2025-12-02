from flask import Flask, request, jsonify
import yt_dlp
import requests

app = Flask(__name__)

# قائمة البروكسيات لتجاوز الحظر
PROXIES = ["https://api.cobalt.tools/api/json", "https://cobalt.api.wuk.sh/api/json"]

def search_youtube(query):
    """البحث في يوتيوب وجلب النتائج كأننا متصفح"""
    ydl_opts = {
        'default_search': 'ytsearch5', # جلب أول 5 نتائج
        'quiet': True,
        'simulate': True,
        'extract_flat': True, # تسريع البحث
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        return info['entries']

@app.route('/api/grab', methods=['POST', 'OPTIONS'])
def handler():
    if request.method == 'OPTIONS':
        return ('', 204, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        })

    data = request.json
    
    # === مود البحث (جديد) ===
    if 'query' in data:
        try:
            results = search_youtube(data['query'])
            return jsonify({'status': 'search', 'results': results}), 200, {'Access-Control-Allow-Origin': '*'}
        except Exception as e:
            return jsonify({'error': str(e)}), 500, {'Access-Control-Allow-Origin': '*'}

    # === مود التحميل (القديم) ===
    url = data.get('url')
    if not url: return jsonify({'error': 'No URL'}), 400

    # 1. المحاولة الخارجية (Cobalt) - للأمان
    headers = {"Accept": "application/json", "Content-Type": "application/json", "User-Agent": "VidGrab/1.0"}
    payload = {"url": url, "vQuality": "max", "filenamePattern": "basic"}

    for proxy in PROXIES:
        try:
            resp = requests.post(proxy, json=payload, headers=headers, timeout=12)
            d = resp.json()
            if 'url' in d or 'picker' in d:
                return jsonify({
                    'status': 'success',
                    'title': d.get('filename'),
                    'url': d.get('url'),
                    'picker': d.get('picker'),
                    'thumbnail': 'https://i.imgur.com/H8q3l5w.png'
                }), 200, {'Access-Control-Allow-Origin': '*'}
        except: continue

    # 2. المحاولة المحلية (yt-dlp) - للطوارئ
    try:
        ydl_opts = {'format': 'best', 'quiet': True, 'simulate': True, 'forceurl': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                'status': 'success',
                'title': info.get('title'),
                'url': info.get('url'),
                'thumbnail': info.get('thumbnail')
            }), 200, {'Access-Control-Allow-Origin': '*'}
    except Exception as e:
        return jsonify({'error': 'فشل التحميل، الرابط محمي.'}), 500, {'Access-Control-Allow-Origin': '*'}
