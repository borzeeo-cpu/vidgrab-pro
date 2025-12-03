from flask import Flask, request, jsonify

app = Flask(__name__)

# ==========================================
# إجبار إضافة هيدرز CORS لكل الردود
# ==========================================
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

# ==========================================
# Route + معالجة OPTIONS
# ==========================================
@app.route('/api/grab', methods=['POST', 'OPTIONS'])
def grab_handler():
    if request.method == "OPTIONS":
        return ("", 200)

    try:
        data = request.json
        
        return jsonify({
            "status": "success",
            "message": "CORS is working perfectly on Vercel!",
            "received_data": data
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run()
