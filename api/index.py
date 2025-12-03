from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import requests
import random

app = Flask(__name__)
# تفعيل CORS كطبقة حماية ثانية
CORS(app)

# قائمة سيرفرات التحميل
COBALT_APIS = [
    "https://api.cobalt.tools/api/json",
    "https://cobalt.api.wuk.sh/api/json",
    "https://api.server.social/api/json",
    "https://cobalt.tools2.net/api/json",
    "https://co2.saveweb.org/api/json"
]

@app.route('/api/grab', methods=['POST', 'OPTIONS'])
def handler():
    # الرد الفوري على طلبات الفحص (OPTIONS)
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")
        return response

    try:
        data = request.json
        
        # 1. البحث (Search)
        if 'query' in data:
            query = data['query']
            ydl_opts = {
                'default_search': 'ytsearch10',
                'quiet': True,
                'simulate': True,
                'extract_flat': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=False)
                results = []
                if 'entries' in info:
                    for entry in info['entries']:
                        if entry:
                            results.append({
                                'title': entry.get('title'),
                                'duration': entry.get('duration_string'),
                                'uploader': entry.get('uploader'),
                                'url': f"https://www.youtube.com/watch?v={entry.get('id')}",
                                'thumbnail': f"https://i.ytimg.com/vi/{entry.get('id')}/mqdefault.jpg"
                            })
                return jsonify({'results': results})

        # 2. التحميل (Download)
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

        return jsonify({'error': 'فشل التحميل من جميع السيرفرات'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# مهم لـ Vercel
if __name__ == '__main__':
    app.run()
