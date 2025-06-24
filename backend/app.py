import os
import json
import redis
import logging
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from config import Config
from gemini_client import GeminiClient
from tasks import process_video_upload, finalize_video
from utils import allowed_file, generate_video_id

# Logging ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask uygulamasını oluştur
app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

# CORS'u daha geniş ayarla (IDX için)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Redis client
try:
    redis_client = redis.from_url(Config.REDIS_URL)
    redis_client.ping()
    app.logger.info("Redis connection successful")
except Exception as e:
    app.logger.error(f"Redis connection failed: {str(e)}")
    redis_client = None

# Gemini client
try:
    gemini_client = GeminiClient()
    app.logger.info("Gemini client initialized")
except Exception as e:
    app.logger.error(f"Gemini client initialization failed: {str(e)}")
    gemini_client = None

@app.route('/api/upload', methods=['POST', 'OPTIONS'])
def upload_video():
    """Video yükleme endpoint'i"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        app.logger.info(f"Upload request received - Files: {request.files.keys()}")
        
        # Dosya kontrolü
        if 'video' not in request.files:
            app.logger.error("No video file in request")
            return jsonify({'error': 'Video dosyası bulunamadı'}), 400
        
        file = request.files['video']
        
        if file.filename == '':
            app.logger.error("Empty filename")
            return jsonify({'error': 'Dosya seçilmedi'}), 400
        
        if not allowed_file(file.filename):
            app.logger.error(f"Invalid file format: {file.filename}")
            return jsonify({'error': 'Geçersiz dosya formatı'}), 400
        
        # Video ID oluştur
        video_id = generate_video_id()
        app.logger.info(f"Generated video ID: {video_id}")
        
        # Güvenli dosya adı oluştur
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower()
        new_filename = f"{video_id}.{file_ext}"
        
        # Upload klasörünün varlığını kontrol et
        if not os.path.exists(Config.UPLOAD_FOLDER):
            os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
            app.logger.info(f"Created upload folder: {Config.UPLOAD_FOLDER}")
        
        # Dosyayı kaydet
        video_path = os.path.join(Config.UPLOAD_FOLDER, new_filename)
        file.save(video_path)
        app.logger.info(f"Video saved to: {video_path}")
        
        # Video işleme görevini başlat (Redis yoksa direkt işle)
        if redis_client:
            task = process_video_upload.delay(video_id, video_path)
            app.logger.info(f"Video processing task queued: {task.id}")
        else:
            # Redis yoksa senkron işle
            app.logger.warning("Redis not available, processing synchronously")
            from utils import get_video_duration
            duration = get_video_duration(video_path)
            
            # Basit bir video info oluştur
            video_info = {
                'id': video_id,
                'path': video_path,
                'duration': duration,
                'status': 'ready'
            }
            
            # Dosyaya kaydet (Redis yerine)
            info_file = os.path.join(Config.UPLOAD_FOLDER, f"{video_id}_info.json")
            with open(info_file, 'w') as f:
                json.dump(video_info, f)
        
        return jsonify({
            'video_id': video_id,
            'message': 'Video yüklendi, işleniyor...'
        }), 200
        
    except Exception as e:
        app.logger.error(f"Upload error: {str(e)}", exc_info=True)
        return jsonify({'error': f'Video yüklenirken hata oluştu: {str(e)}'}), 500

# Log endpoint'i ekle
@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Log dosyasını görüntüle"""
    try:
        log_file_path = os.path.join(Config.LOG_FOLDER, Config.LOG_FILE)
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r') as f:
                logs = f.read()
            return jsonify({'logs': logs}), 200
        else:
            return jsonify({'logs': 'No logs found'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/<video_id>', methods=['POST'])
def chat_with_ai(video_id):
    """AI ile sohbet endpoint'i"""
    try:
        # İstek verilerini al
        data = request.get_json()
        user_prompt = data.get('prompt', '')
        
        if not user_prompt:
            app.logger.error("Empty prompt received")
            return jsonify({'error': 'Mesaj boş olamaz'}), 400
        
        # Video bilgilerini kontrol et
        video_info_str = redis_client.get(f'video_info:{video_id}')
        if not video_info_str:
            app.logger.error(f"Video info not found for video_id: {video_id}")
            return jsonify({'error': 'Video bulunamadı'}), 404
        
        video_info = json.loads(video_info_str)
        video_path = video_info['path']
        
        # Konuşma geçmişini al
        chat_history_key = f'chat_history:{video_id}'
        chat_history_str = redis_client.get(chat_history_key)
        
        if chat_history_str:
            # Mevcut konuşmaya devam et
            chat_data = json.loads(chat_history_str)
            chat_history = chat_data['contents']
            previous_response = chat_data['last_response']
            
            response, updated_contents, raw_response = gemini_client.continue_conversation(
                chat_history,
                previous_response,
                user_prompt
            )
        else:
            # Yeni konuşma başlat
            response, updated_contents, raw_response = gemini_client.start_conversation(
                video_path,
                user_prompt
            )
        
        # Konuşma geçmişini güncelle ve kaydet
        if updated_contents and raw_response:
            chat_data = {
                'contents': updated_contents,
                'last_response': raw_response
            }
            # Contents listesi JSON serialize edilemeyebilir, bu yüzden basitleştirilmiş versiyonu kaydet
            redis_client.setex(
                chat_history_key,
                3600,  # 1 saat
                json.dumps(chat_data, default=str)
            )
        
        # Video süresini ekle
        response['video_duration'] = video_info['duration']
        
        app.logger.info(f"Chat response sent for video_id: {video_id}")
        return jsonify(response), 200
        
    except Exception as e:
        app.logger.error(f"Chat error for video_id {video_id}: {str(e)}", exc_info=True)
        return jsonify({
            'cuts': [],
            'message': 'Bir hata oluştu, lütfen tekrar deneyin.'
        }), 500

@app.route('/api/status/<video_id>', methods=['GET'])
def get_video_status(video_id):
    """Video işleme durumunu sorgula"""
    try:
        # Durum bilgisini al
        status_str = redis_client.get(f'video_status:{video_id}')
        
        if status_str:
            status_data = json.loads(status_str)
            app.logger.info(f"Status request for video_id {video_id}: {status_data['status']}")
            return jsonify(status_data), 200
        else:
            # Video bilgilerini kontrol et
            video_info_str = redis_client.get(f'video_info:{video_id}')
            if video_info_str:
                app.logger.info(f"Video info found for video_id {video_id}, status ready")
                return jsonify({
                    'status': 'ready',
                    'message': 'Video hazır'
                }), 200
            else:
                app.logger.warning(f"Video not found for video_id: {video_id}")
                return jsonify({
                    'status': 'not_found',
                    'message': 'Video bulunamadı'
                }), 404
                
    except Exception as e:
        app.logger.error(f"Status error for video_id {video_id}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Durum sorgulanırken hata oluştu'}), 500

@app.route('/api/finalize', methods=['POST'])
def finalize_video_endpoint():
    """Video kesim ve birleştirme işlemini başlat"""
    try:
        # İstek verilerini al
        data = request.get_json()
        video_id = data.get('video_id')
        cuts = data.get('cuts', [])
        
        if not video_id:
            app.logger.error("Video ID not provided for finalize request")
            return jsonify({'error': 'Video ID gerekli'}), 400
        
        if not cuts:
            app.logger.error("No cuts provided for finalize request")
            return jsonify({'error': 'En az bir kesim gerekli'}), 400
        
        # Video bilgilerini kontrol et
        video_info_str = redis_client.get(f'video_info:{video_id}')
        if not video_info_str:
            app.logger.error(f"Video info not found for finalize video_id: {video_id}")
            return jsonify({'error': 'Video bulunamadı'}), 404
        
        # Birleştirme görevini başlat
        task = finalize_video.delay(video_id, cuts)
        
        app.logger.info(f"Finalize task queued for video_id: {video_id}, task_id: {task.id}")
        return jsonify({
            'video_id': video_id,
            'task_id': task.id,
            'message': 'Video işleniyor...'
        }), 200
        
    except Exception as e:
        app.logger.error(f"Finalize error for video_id {video_id}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Video işlenirken hata oluştu'}), 500

@app.route('/api/download/<video_id>', methods=['GET'])
def download_video(video_id):
    """İşlenmiş videoyu indir"""
    try:
        # Sonuç bilgilerini al
        result_str = redis_client.get(f'video_result:{video_id}')
        
        if not result_str:
            app.logger.error(f"Processed video result not found for video_id: {video_id}")
            return jsonify({'error': 'İşlenmiş video bulunamadı'}), 404
        
        result_info = json.loads(result_str)
        output_path = result_info['output_path']
        
        if not os.path.exists(output_path):
            app.logger.error(f"Output video file not found at path: {output_path}")
            return jsonify({'error': 'Video dosyası bulunamadı'}), 404
        
        app.logger.info(f"Serving download for video_id: {video_id} from {output_path}")
        return send_file(
            output_path,
            as_attachment=True,
            download_name=f'edited_{video_id}.mp4',
            mimetype='video/mp4'
        )
        
    except Exception as e:
        app.logger.error(f"Download error for video_id {video_id}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Video indirilirken hata oluştu'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Sağlık kontrolü endpoint'i"""
    try:
        # Redis bağlantısını kontrol et
        redis_client.ping()
        
        app.logger.info("Health check: Redis connected")
        return jsonify({
            'status': 'healthy',
            'redis': 'connected'
        }), 200
        
    except Exception as e:
        app.logger.error(f"Health check: Redis disconnected - {str(e)}", exc_info=True)
        return jsonify({
            'status': 'unhealthy',
            'redis': 'disconnected'
        }), 500

if __name__ == '__main__':
    # Project IDX için port ayarı
    import os
    port = int(os.environ.get('PORT', 5000))
    app.logger.info(f"Starting Flask app on port {port}")
    app.run(debug=True, host='0.0.0.0', port=port)
