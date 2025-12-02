from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import requests
import random

app = Flask(__name__)
# هذا السطر السحري يحل مشكلة Failed to fetch
CORS(app, resources={r"/*": {"origins": "*"}})

# سيرفرات التحميل (Cobalt)
COBALT_APIS = [
    "https://api.cobalt.tools/api/json",
    "https://cobalt.api.wuk.sh/api/json",
    "https://api.server.social/api/json",
    "https://cobalt.tools2.net/api/json",
    "https://co2.saveweb.org/api/json"
]

def search_youtube(query):
    """بحث سريع وآمن"""
    ydl_opts = {
        'default_search': 'ytsearch10',
        'quiet': True,
        'simulate': True,
        'extract_flat': True, # يجلب العناوين فقط بسرعة
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            results = []
            if 'entries' in info:
                for entry in info['entries']:
                    if not entry: continue
                    results.append({
                        'title': entry.get('title'),
                        'duration': entry.get('duration_string'),
                        'uploader': entry.get('uploader'),
                        'url': f"https://www.youtube.com/watch?v={entry.get('id')}",
                        'thumbnail': f"https://i.ytimg.com/vi/{entry.get('id')}/mqdefault.jpg"
                    })
            return results
    except:
        return []

@app.route('/api/grab', methods=['POST', 'OPTIONS'])
def handler():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    data = request.json
    
    # 1. لو المستخدم بيبحث (عشان نعرض له فيديوهات زي SnapTube)
    if 'query' in data:
        results = search_youtube(data['query'])
        return jsonify({'results': results})

    # 2. لو المستخدم اختار فيديو وعاوز يحمله
    url = data.get('url')
    if not url: return jsonify({'error': 'No URL'}), 400

    random.shuffle(COBALT_APIS)
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "VidGrab/App"
    }

    payload = {
        "url": url,
        "videoQuality": "max",
        "filenamePattern": "basic",
        "youtubeVideoCodec": "h264"
    }

    for api in COBALT_APIS:
        try:
            r = requests.post(api, json=payload, headers=headers, timeout=9)
            if r.status_code == 200:
                d = r.json()
                if 'url' in d or 'picker' in d:
                    return jsonify({
                        'status': 'success',
                        'title': d.get('filename'),
                        'url': d.get('url'),
                        'picker': d.get('picker'),
                        'thumbnail': 'https://placehold.co/600x400/000/FFF?text=Ready'
                    })
        except:
            continue

    return jsonify({'error': 'فشل التحميل، حاول مرة أخرى'}), 500

# ضروري لـ Vercel
if __name__ == '__main__':
    app.run()
