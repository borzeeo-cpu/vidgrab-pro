from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

@app.route('/api/grab', methods=['GET', 'POST'])
def grab_video():
    # استقبال الرابط
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

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
                'thumbnail': info.get('thumbnail')
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
