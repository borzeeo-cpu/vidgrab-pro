const ytdl = require('ytdl-core');

// دالة لمعالجة الطلبات (Vercel Serverless Function)
export default async function handler(req, res) {
    
    // 1. حل مشكلة CORS نهائياً (يدوياً)
    res.setHeader('Access-Control-Allow-Credentials', true);
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,POST');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Accept');

    // الرد السريع على فحص الاتصال
    if (req.method === 'OPTIONS') {
        res.status(200).end();
        return;
    }

    try {
        const { url } = req.body;

        if (!url) {
            return res.status(400).json({ error: 'No URL provided' });
        }

        // ==========================================
        // أ) إذا كان الرابط يوتيوب -> استخدم ytdl-core
        // ==========================================
        if (ytdl.validateURL(url)) {
            try {
                const info = await ytdl.getInfo(url);
                
                // اختيار أفضل صيغة (فيديو + صوت)
                // ytdl-core يفصل الصوت عن الفيديو أحياناً، سنحاول جلب صيغة مدمجة
                const format = ytdl.chooseFormat(info.formats, { quality: '18' }); // 18 هي mp4 360p (مضمونة العمل)
                // أو نختار أعلى جودة متاحة
                const bestFormat = ytdl.chooseFormat(info.formats, { quality: 'highest' });

                return res.status(200).json({
                    status: 'success',
                    title: info.videoDetails.title,
                    url: format.url || bestFormat.url,
                    thumbnail: info.videoDetails.thumbnails.pop().url, // آخر صورة تكون الأوضح
                    source: 'ytdl-core (Node.js)'
                });
            } catch (ytError) {
                // إذا فشل ytdl-core (بسبب تحديثات يوتيوب)، سننتقل للخطة (ب) تلقائياً
                console.log("ytdl-core failed, switching to fallback...");
            }
        }

        // ==========================================
        // ب) باقي المواقع (أو فشل يوتيوب) -> Cobalt API
        // ==========================================
        const cobaltResponse = await fetch("https://api.cobalt.tools/api/json", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "VidGrab/Node"
            },
            body: JSON.stringify({
                url: url,
                videoQuality: "max",
                filenamePattern: "basic"
            })
        });
        
        const data = await cobaltResponse.json();
        
        if (data.url || data.picker) {
             return res.status(200).json({
                status: 'success',
                title: data.filename || 'Video Download',
                url: data.url || (data.picker ? data.picker[0].url : null),
                thumbnail: 'https://placehold.co/600x400/000/FFF?text=Video',
                source: 'External API'
            });
        }

        throw new Error('فشل التحميل، الرابط غير مدعوم أو محظور');

    } catch (error) {
        return res.status(500).json({ 
            error: error.message || 'Server Error' 
        });
    }
}
