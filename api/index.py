from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import requests
import random
from gallery_dl import job

app = Flask(__name__)
# تفعيل CORS للجميع
CORS(app, resources={r"/*": {"origins": "*"}})

# ==========================================
# 1. محرك البحث (Invidious API)
# نستخدمه بدلاً من yt-dlp للبحث لأنه أسرع 10 مرات ولا يُحظر
# ==========================================
INVIDIOUS_INSTANCES = [
    "https://inv.tux.pizza",
    "https://invidious.drgns.space",
    "https://vid.puffyan.us",
    "https://invidious.fdn.fr"
]

def search_invidious(query):
    for instance in INVIDIOUS_INSTANCES:
        try:
            # البحث عن فيديوهات فقط
            url = f"{instance}/api/v1/search?q={query}&type=video&sort=relevance"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                results = []
                for item in data:
                    if item.get('type') == 'video':
                        results.append({
                            'title': item.get('title'),
                            'uploader': item.get('author'),
                            'duration': convert_seconds(item.get('lengthSeconds', 0)),
                            'thumbnail': item.get('videoThumbnails')[1]['url'] if item.get('videoThumbnails') else None,
                            'url': f"https://www.youtube.com/watch?v={item.get('videoId')}"
                        })
                return results
        except:
            continue
    return []

def convert_seconds(seconds):
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0: return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

# ==========================================
# 2. محرك الصور (Gallery-dl)
# ==========================================
def grab_gallery(url):
    # gallery-dl مصمم للعمل كـ CLI، لذا استخدامه كـ Library معقد قليلاً
    # سنستخدم yt-dlp للصور أيضاً لأنه يدعم Instagram/Twitter بكفاءة أعلى في Vercel
    # أو نستخدم Cobalt لأنه يدعم الصور
    return None

# ==========================================
# 3. محرك الفيديو (Cobalt + yt-dlp)
# ==========================================
COBALT_APIS = [
    "https://api.cobalt.tools/api/json",
    "https://cobalt.api.wuk.sh/api/json",
    "https://api.server.social/api/json"
]

def grab_video_cobalt(url):
    random.shuffle(COBALT_APIS)
    headers = {"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "VidGrab/Ultra"}
    payload = {"url": url, "videoQuality": "max", "filenamePattern": "basic"}

    for api in COBALT_APIS:
        try:
            r = requests.post(api, json=payload, headers=headers, timeout=10)
            if r.status_code == 200:
                d = r.json()
                if 'url' in d or 'picker' in d:
                    return {
                        'status': 'success',
                        'title': d.get('filename', 'Media'),
                        'url': d.get('url'),
                        'picker': d.get('picker'),
                        'thumbnail': 'https://placehold.co/600x400/000/FFF?text=Media+Ready',
                        'source': 'cobalt'
                    }
        except: continue
    return None

def grab_video_ytdlp(url):
    # محاولة محلية أخيرة
    ydl_opts = {'format': 'best', 'quiet': True, 'simulate': True, 'forceurl': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'status': 'success',
                'title': info.get('title'),
                'url': info.get('url'),
                'thumbnail': info.get('thumbnail'),
                'source': 'ytdlp_local'
            }
    except Exception as e:
        return None

# ==========================================
# الموجه الرئيسي (Main Handler)
# ==========================================
@app.route('/api/grab', methods=['POST', 'OPTIONS'])
def handler():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    try:
        data = request.json
        
        # --- طلب بحث ---
        if 'query' in data:
            # نستخدم Invidious بدلاً من yt-dlp للسرعة وعدم الحظر
            results = search_invidious(data['query'])
            return jsonify({'results': results})

        # --- طلب تحميل ---
        url = data.get('url')
        if not url: return jsonify({'error': 'No URL'}), 400

        # الاستراتيجية:
        # 1. جرب Cobalt (الأسرع والأقوى للفيديوهات)
        result = grab_video_cobalt(url)
        if result: return jsonify(result)

        # 2. جرب yt-dlp (للمواقع الغريبة التي لا يدعمها Cobalt)
        result = grab_video_ytdlp(url)
        if result: return jsonify(result)

        return jsonify({'error': 'فشل التحميل من جميع المصادر'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run()
