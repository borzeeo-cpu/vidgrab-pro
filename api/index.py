from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

@app.route('/api/grab', methods=['GET', 'POST', 'OPTIONS'])
def handler():
    # 1. إعدادات السماح (CORS) عشان التطبيق يشتغل
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
        return ('', 204, headers)

    # استقبال الرابط
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    # 2. إعدادات yt-dlp (استخراج الرابط فقط)
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'simulate': True, # لا تحمل الفيديو، هات الرابط بس
        'forceurl': True,
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            return jsonify({
                'status': 'success',
                'title': info.get('title'),
                'url': info.get('url'), # الرابط المباشر
                'thumbnail': info.get('thumbnail')
            }), 200, {'Access-Control-Allow-Origin': '*'}

    except Exception as e:
        return jsonify({'error': str(e)}), 500, {'Access-Control-Allow-Origin': '*'}
