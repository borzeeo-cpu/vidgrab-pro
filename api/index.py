from flask import Flask, request, jsonify
import yt_dlp
import requests
import json

app = Flask(__name__)

# قائمة سيرفرات بديلة قوية
PROXIES = [
    "https://cobalt.api.wuk.sh", 
    "https://api.cobalt.tools",
    "https://api.server.social"
]

def solve_youtube_proxy(url):
    """دالة خاصة لليوتيوب تستخدم سيرفرات خارجية لتجنب الحظر"""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    
    payload = {
        "url": url,
        "videoQuality": "max",
        "filenamePattern": "basic"
    }

    for domain in PROXIES:
        try:
            # ضبط الرابط حسب السيرفر
            api_url = f"{domain}/api/json"
            
            # محاولة الاتصال
            resp = requests.post(api_url, json=payload, headers=headers, timeout=10)
            data = resp.json()

            # فحص النجاح
            if 'url' in data or 'picker' in data:
                return {
                    'status': 'success',
                    'title': data.get('filename', 'YouTube Video'),
                    'url': data.get('url'),
                    'picker': data.get('picker'),
                    'thumbnail': 'https://i.imgur.com/H8q3l5w.png',
                    'source': 'proxy'
                }
        except Exception as e:
            continue # فشل هذا السيرفر، جرب التالي

    return None

@app.route('/api/grab', methods=['POST', 'OPTIONS'])
def grab_video():
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
        return ('', 204, headers)

    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    # 🛑 توجيه ذكي 🛑
    
    # 1. يوتيوب (محظور محلياً) -> استخدم البروكسي الإجباري
    if "youtube.com" in url or "youtu.be" in url:
        result = solve_youtube_proxy(url)
        if result:
            return jsonify(result), 200, {'Access-Control-Allow-Origin': '*'}
        else:
            return jsonify({'error': 'سيرفرات يوتيوب مشغولة حالياً، حاول مرة أخرى لاحقاً'}), 503, {'Access-Control-Allow-Origin': '*'}

    # 2. تيك توك / انستا / فيسبوك -> استخدم yt-dlp المحلي (يعمل بامتياز)
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'simulate': True,
        'forceurl': True,
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                'status': 'success',
                'title': info.get('title'),
                'url': info.get('url'),
                'thumbnail': info.get('thumbnail'),
                'source': 'local'
            }), 200, {'Access-Control-Allow-Origin': '*'}

    except Exception as e:
        return jsonify({'error': str(e)}), 500, {'Access-Control-Allow-Origin': '*'}
