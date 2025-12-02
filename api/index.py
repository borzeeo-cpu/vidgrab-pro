from flask import Flask, request, jsonify
import yt_dlp
import requests

app = Flask(__name__)

# قائمة البروكسيات للتحميل
PROXIES = [
    "https://api.cobalt.tools", 
    "https://cobalt.api.wuk.sh",
    "https://api.server.social"
]

def search_youtube_robust(query):
    """بحث قوي يتجاوز الحظر"""
    ydl_opts = {
        'default_search': 'ytsearch10', # جلب 10 نتائج
        'quiet': True,
        'simulate': True,
        'extract_flat': True, # المفتاح السحري: يجلب البيانات دون فحص الفيديو بعمق (أسرع ولا يُحظر)
        'skip_download': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            
            # تنسيق النتائج
            if 'entries' in info:
                results = []
                for entry in info['entries']:
                    if not entry: continue
                    results.append({
                        'id': entry.get('id'),
                        'title': entry.get('title'),
                        'uploader': entry.get('uploader'),
                        'duration': entry.get('duration'),
                        'duration_string': entry.get('duration_string'),
                        'view_count': entry.get('view_count'),
                        # بناء رابط الصورة يدوياً لتقليل الطلبات
                        'thumbnail': f"https://i.ytimg.com/vi/{entry.get('id')}/mqdefault.jpg",
                        'url': f"https://www.youtube.com/watch?v={entry.get('id')}"
                    })
                return results
    except Exception as e:
        print(f"Search Error: {e}")
        return []
    return []

def get_direct_link_proxy(url):
    """محاولة جلب الرابط المباشر عبر Cobalt"""
    headers = {"Accept": "application/json", "Content-Type": "application/json", "User-Agent": "VidGrab/2.0"}
    
    # تحسين إعدادات تيك توك ويوتيوب
    payload = {
        "url": url,
        "videoQuality": "max",
        "filenamePattern": "basic",
        "youtubeVideoCodec": "h264",
        "audioFormat": "mp3",
        "tiktokH265": False
    }

    for domain in PROXIES:
        try:
            target = f"{domain}/api/json"
            resp = requests.post(target, json=payload, headers=headers, timeout=12)
            data = resp.json()
            
            if 'url' in data or 'picker' in data:
                return {
                    'status': 'success',
                    'title': data.get('filename'),
                    'url': data.get('url'),
                    'picker': data.get('picker'),
                    'thumbnail': 'https://placehold.co/600x400/000/FFF?text=Video+Ready'
                }
        except: continue
    
    return None

@app.route('/api/grab', methods=['POST', 'OPTIONS'])
def handler():
    if request.method == 'OPTIONS':
        return ('', 204, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        })

    data = request.json
    
    # 1. طلب البحث
    if 'query' in data:
        results = search_youtube_robust(data['query'])
        if not results:
            return jsonify({'error': 'No results found or search blocked'}), 404, {'Access-Control-Allow-Origin': '*'}
        return jsonify({'results': results}), 200, {'Access-Control-Allow-Origin': '*'}

    # 2. طلب التحميل/التشغيل
    url = data.get('url')
    if not url: return jsonify({'error': 'No URL'}), 400

    # المحاولة الخارجية (Cobalt) - الخيار الأفضل
    proxy_res = get_direct_link_proxy(url)
    if proxy_res:
        return jsonify(proxy_res), 200, {'Access-Control-Allow-Origin': '*'}

    # المحاولة المحلية (yt-dlp) - للطوارئ (تيك توك فقط)
    try:
        ydl_opts = {'format': 'best', 'quiet': True, 'simulate': True, 'forceurl': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                'title': info.get('title'),
                'url': info.get('url'),
                'thumbnail': info.get('thumbnail')
            }), 200, {'Access-Control-Allow-Origin': '*'}
    except Exception as e:
        return jsonify({'error': str(e)}), 500, {'Access-Control-Allow-Origin': '*'}
