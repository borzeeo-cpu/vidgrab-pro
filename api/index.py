from flask import Flask, request, jsonify
import yt_dlp
import requests
import random

app = Flask(__name__)

# قائمة سيرفرات Cobalt القوية (تعمل كبديل لليوتيوب)
COBALT_INSTANCES = [
    "https://cobalt.api.wuk.sh",      # قوي جداً
    "https://api.cobalt.tools",       # الرسمي
    "https://api.server.social",      # احتياطي
    "https://cobalt.tools"
]

def solve_with_cobalt(url):
    """دالة لتحويل طلبات يوتيوب لسيرفرات خارجية"""
    payload = {
        "url": url,
        "vQuality": "max",
        "filenamePattern": "basic",
        "isAudioOnly": False
    }
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "VidGrab-App/1.0"
    }

    # نجرب السيرفرات بالترتيب
    for instance in COBALT_INSTANCES:
        try:
            # Cobalt v10 endpoint
            api_url = f"{instance}/api/json" if "tools" in instance else instance
            if not api_url.endswith("/api/json") and "wuk" not in instance:
                 api_url = f"{instance}/api/json"
            
            # Wuk.sh uses a direct endpoint usually
            if "wuk.sh" in instance:
                api_url = "https://cobalt.api.wuk.sh/api/json"

            # محاولة الاتصال
            resp = requests.post(api_url, json=payload, headers=headers, timeout=8)
            data = resp.json()

            if 'url' in data or 'picker' in data:
                return {
                    'status': 'success',
                    'title': data.get('filename', 'YouTube Video'),
                    'url': data.get('url'),
                    'picker': data.get('picker'),
                    'thumbnail': 'https://i.imgur.com/H8q3l5w.png', # صورة افتراضية لليوتيوب
                    'source': 'external_proxy'
                }
        except Exception as e:
            continue # فشل هذا السيرفر، جرب التالي
    
    return None

@app.route('/api/grab', methods=['POST', 'OPTIONS'])
def grab_video():
    # إعدادات السماح (CORS)
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

    # 🛑 استراتيجية التوجيه الذكي 🛑
    
    # 1. إذا كان يوتيوب -> استخدم السيرفرات الخارجية (لتجنب الحظر)
    if "youtube.com" in url or "youtu.be" in url:
        result = solve_with_cobalt(url)
        if result:
            return jsonify(result), 200, {'Access-Control-Allow-Origin': '*'}
        # إذا فشلت السيرفرات الخارجية، سنحاول محلياً كحل أخير
    
    # 2. باقي المواقع (TikTok, Insta) أو فشل الخارجي -> استخدم yt-dlp المحلي
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'simulate': True,
        'forceurl': True,
        'noplaylist': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            return jsonify({
                'status': 'success',
                'title': info.get('title'),
                'url': info.get('url'),
                'thumbnail': info.get('thumbnail'),
                'source': 'local_engine'
            }), 200, {'Access-Control-Allow-Origin': '*'}

    except Exception as e:
        error_msg = str(e)
        if "Sign in" in error_msg:
             return jsonify({'error': 'يوتيوب يحظر السيرفر حالياً، يرجى المحاولة لاحقاً'}), 500, {'Access-Control-Allow-Origin': '*'}
        
        return jsonify({'error': str(e)}), 500, {'Access-Control-Allow-Origin': '*'}
