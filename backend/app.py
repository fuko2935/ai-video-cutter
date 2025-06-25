import os
import json
import redis
import logging
import uuid
import time
from flask import Flask, request, jsonify, send_file, g
from flask_cors import CORS
from werkzeug.utils import secure_filename
from config import Config
from logging_config import setup_logging, log_execution_time, log_api_request, get_logger
from gemini_client import GeminiClient
from tasks import process_video_upload, finalize_video
from utils import allowed_file, generate_video_id

# Loglama sistemini başlat
setup_logging(log_level='DEBUG')
logger = get_logger(__name__)

# Flask uygulamasını oluştur
app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

logger.info("Flask application starting...")
logger.debug(f"Configuration loaded: UPLOAD_FOLDER={Config.UPLOAD_FOLDER}")

# CORS'u daha geniş ayarla
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})
logger.info("CORS configured")

# Redis client
try:
    redis_client = redis.from_url(Config.REDIS_URL)
    redis_client.ping()
    logger.info("✅ Redis connection successful")
except Exception as e:
    logger.error(f"❌ Redis connection failed: {str(e)}", exc_info=True)
    redis_client = None

# Gemini client
try:
    gemini_client = GeminiClient()
    logger.info("✅ Gemini client initialized")
except Exception as e:
    logger.error(f"❌ Gemini client initialization failed: {str(e)}", exc_info=True)
    gemini_client = None

@app.before_request
def before_request():
    """Her request öncesi çalışır"""
    g.start_time = time.time()
    g.request_id = str(uuid.uuid4())
    request.request_id = g.request_id
    
    logger.debug(
        f"🔵 Request started: {request.method} {request.path}",
        extra={'request_id': g.request_id}
    )

@app.after_request
def after_request(response):
    """Her request sonrası çalışır"""
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        log_api_request(request, response, duration)
        
        logger.debug(
            f"✅ Request completed: {request.method} {request.path} - "
            f"Status: {response.status_code} - Duration: {duration:.3f}s",
            extra={'request_id': g.request_id, 'duration': duration}
        )
    
    return response

@app.errorhandler(Exception)
def handle_error(error):
    """Global error handler"""
    logger.error(
        f"❌ Unhandled exception: {str(error)}",
        exc_info=True,
        extra={'request_id': getattr(g, 'request_id', None)}
    )
    
    return jsonify({
        'error': 'Internal server error',
        'message': str(error) if app.debug else 'An error occurred',
        'request_id': getattr(g, 'request_id', None)
    }), 500

@app.route('/api/upload', methods=['POST', 'OPTIONS'])
@log_execution_time()
def upload_video():
    """Video yükleme endpoint'i"""
    if request.method == 'OPTIONS':
        return '', 200
    
    video_id = None
    
    try:
        logger.info(f"📤 Upload request received", extra={'request_id': g.request_id})
        logger.debug(f"Request files: {list(request.files.keys())}")
        logger.debug(f"Request headers: {dict(request.headers)}")
        
        # Dosya kontrolü
        if 'video' not in request.files:
            logger.warning("❌ No video file in request")
            return jsonify({'error': 'Video dosyası bulunamadı'}), 400
        
        file = request.files['video']
        logger.info(f"📹 File received: {file.filename}, Size: {file.content_length} bytes")
        
        if file.filename == '':
            logger.warning("❌ Empty filename")
            return jsonify({'error': 'Dosya seçilmedi'}), 400
        
        if not allowed_file(file.filename):
            logger.warning(f"❌ Invalid file format: {file.filename}")
            return jsonify({'error': 'Geçersiz dosya formatı'}), 400
        
        # Video ID oluştur
        video_id = generate_video_id()
        logger.info(f"🆔 Generated video ID: {video_id}")
        
        # Güvenli dosya adı oluştur
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower()
        new_filename = f"{video_id}.{file_ext}"
        
        # Upload klasörünün varlığını kontrol et
        if not os.path.exists(Config.UPLOAD_FOLDER):
            os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
            logger.info(f"📁 Created upload folder: {Config.UPLOAD_FOLDER}")
        
        # Dosyayı kaydet
        video_path = os.path.join(Config.UPLOAD_FOLDER, new_filename)
        logger.debug(f"💾 Saving video to: {video_path}")
        
        file.save(video_path)
        file_size = os.path.getsize(video_path)
        logger.info(f"✅ Video saved successfully: {video_path} ({file_size} bytes)")
        
        # Video işleme görevini başlat
        if redis_client:
            task = process_video_upload.delay(video_id, video_path)
            logger.info(f"📋 Video processing task queued: {task.id}")
        else:
            logger.warning("⚠️ Redis not available, processing synchronously")
            from utils import get_video_duration
            
            duration = get_video_duration(video_path)
            logger.info(f"⏱️ Video duration: {duration} seconds")
            
            # Video info oluştur
            video_info = {
                'id': video_id,
                'path': video_path,
                'duration': duration,
                'status': 'ready',
                'filename': file.filename,
                'size': file_size
            }
            
            # Dosyaya kaydet
            info_file = os.path.join(Config.UPLOAD_FOLDER, f"{video_id}_info.json")
            with open(info_file, 'w') as f:
                json.dump(video_info, f)
            logger.debug(f"📄 Video info saved to: {info_file}")
        
        logger.info(
            f"✅ Upload completed successfully",
            extra={'video_id': video_id, 'duration': time.time() - g.start_time}
        )
        
        return jsonify({
            'video_id': video_id,
            'message': 'Video yüklendi, işleniyor...'
        }), 200
        
    except Exception as e:
        logger.error(
            f"❌ Upload error: {str(e)}",
            exc_info=True,
            extra={
                'video_id': video_id,
                'request_id': g.request_id
            }
        )
        return jsonify({'error': f'Video yüklenirken hata oluştu: {str(e)}'}), 500

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Log dosyalarını görüntüle"""
    try:
        log_type = request.args.get('type', 'general')
        lines = int(request.args.get('lines', 100))
        
        log_files = {
            'general': 'logs/app/general.log',
            'debug': 'logs/app/debug.log',
            'error': 'logs/errors/errors.log',
            'api': 'logs/api/requests.log',
            'performance': 'logs/app/performance.log'
        }
        
        log_file = log_files.get(log_type, 'logs/app/general.log')
        
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = f.readlines()[-lines:]
            
            return jsonify({
                'logs': ''.join(logs),
                'type': log_type,
                'file': log_file
            }), 200
        else:
            return jsonify({'logs': 'Log file not found', 'file': log_file}), 404
            
    except Exception as e:
        logger.error(f"Log read error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/<video_id>', methods=['POST'])
@log_execution_time()
def chat_with_ai(video_id):
    """AI ile sohbet endpoint'i"""
    try:
        logger.info(f"💬 Chat request received for video_id: {video_id}", extra={'video_id': video_id, 'request_id': g.request_id})
        # İstek verilerini al
        data = request.get_json()
        user_prompt = data.get('prompt', '')
        
        if not user_prompt:
            logger.warning("❌ Empty prompt received")
            return jsonify({'error': 'Mesaj boş olamaz'}), 400
        
        # Video bilgilerini kontrol et
        video_info_str = redis_client.get(f'video_info:{video_id}')
        if not video_info_str:
            logger.warning(f"❌ Video info not found for video_id: {video_id}")
            return jsonify({'error': 'Video bulunamadı'}), 404
        
        video_info = json.loads(video_info_str)
        video_path = video_info['path']
        
        logger.debug(f"Video path: {video_path}")

        # Konuşma geçmişini al
        chat_history_key = f'chat_history:{video_id}'
        chat_history_str = redis_client.get(chat_history_key)
        
        if chat_history_str:
            logger.debug("Continuing existing conversation")
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
            logger.debug("Starting new conversation")
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
            logger.debug(f"Chat history updated for video_id: {video_id}")
        
        # Video süresini ekle
        response['video_duration'] = video_info['duration']
        
        logger.info(f"✅ Chat response sent for video_id: {video_id}", extra={'video_id': video_id})
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"❌ Chat error for video_id {video_id}: {str(e)}", exc_info=True, extra={'video_id': video_id, 'request_id': g.request_id})
        return jsonify({
            'cuts': [],
            'message': 'Bir hata oluştu, lütfen tekrar deneyin.'
        }), 500

@app.route('/api/status/<video_id>', methods=['GET'])
@log_execution_time()
def get_video_status(video_id):
    """Video işleme durumunu sorgula"""
    try:
        logger.info(f"📊 Status request received for video_id: {video_id}", extra={'video_id': video_id, 'request_id': g.request_id})
        # Durum bilgisini al
        status_str = redis_client.get(f'video_status:{video_id}')
        
        if status_str:
            status_data = json.loads(status_str)
            logger.debug(f"Status data from Redis: {status_data}")
            logger.info(f"✅ Status for video_id {video_id}: {status_data['status']}", extra={'video_id': video_id, 'status': status_data['status']})
            return jsonify(status_data), 200
        else:
            # Video bilgilerini kontrol et
            video_info_str = redis_client.get(f'video_info:{video_id}')
            if video_info_str:
                logger.info(f"Video info found for video_id {video_id}, status ready", extra={'video_id': video_id, 'status': 'ready'})
                return jsonify({
                    'status': 'ready',
                    'message': 'Video hazır'
                }), 200
            else:
                logger.warning(f"❌ Video not found for video_id: {video_id}")
                return jsonify({
                    'status': 'not_found',
                    'message': 'Video bulunamadı'
                }), 404
                
    except Exception as e:
        logger.error(f"❌ Status error for video_id {video_id}: {str(e)}", exc_info=True, extra={'video_id': video_id, 'request_id': g.request_id})
        return jsonify({'error': 'Durum sorgulanırken hata oluştu'}), 500

@app.route('/api/finalize', methods=['POST'])
@log_execution_time()
def finalize_video_endpoint():
    """Video kesim ve birleştirme işlemini başlat"""
    try:
        logger.info(f"✂️ Finalize request received", extra={'request_id': g.request_id})
        # İstek verilerini al
        data = request.get_json()
        video_id = data.get('video_id')
        cuts = data.get('cuts', [])
        
        logger.debug(f"Finalize request data: video_id={video_id}, cuts_count={len(cuts)}")

        if not video_id:
            logger.warning("❌ Video ID not provided for finalize request")
            return jsonify({'error': 'Video ID gerekli'}), 400
        
        if not cuts:
            logger.warning("❌ No cuts provided for finalize request")
            return jsonify({'error': 'En az bir kesim gerekli'}), 400
        
        # Video bilgilerini kontrol et
        video_info_str = redis_client.get(f'video_info:{video_id}')
        if not video_info_str:
            logger.warning(f"❌ Video info not found for finalize video_id: {video_id}")
            return jsonify({'error': 'Video bulunamadı'}), 404
        
        # Birleştirme görevini başlat
        task = finalize_video.delay(video_id, cuts)
        
        logger.info(f"✅ Finalize task queued for video_id: {video_id}, task_id: {task.id}", extra={'video_id': video_id, 'task_id': task.id})
        return jsonify({
            'video_id': video_id,
            'task_id': task.id,
            'message': 'Video işleniyor...'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Finalize error for video_id {video_id}: {str(e)}", exc_info=True, extra={'video_id': video_id, 'request_id': g.request_id})
        return jsonify({'error': 'Video işlenirken hata oluştu'}), 500

@app.route('/api/download/<video_id>', methods=['GET'])
@log_execution_time()
def download_video(video_id):
    """İşlenmiş videoyu indir"""
    try:
        logger.info(f"⬇️ Download request received for video_id: {video_id}", extra={'video_id': video_id, 'request_id': g.request_id})
        # Sonuç bilgilerini al
        result_str = redis_client.get(f'video_result:{video_id}')
        
        if not result_str:
            logger.warning(f"❌ Processed video result not found for video_id: {video_id}")
            return jsonify({'error': 'İşlenmiş video bulunamadı'}), 404
        
        result_info = json.loads(result_str)
        output_path = result_info['output_path']
        
        if not os.path.exists(output_path):
            logger.warning(f"❌ Output video file not found at path: {output_path}")
            return jsonify({'error': 'Video dosyası bulunamadı'}), 404
        
        logger.info(f"✅ Serving download for video_id: {video_id} from {output_path}", extra={'video_id': video_id, 'output_path': output_path})
        return send_file(
            output_path,
            as_attachment=True,
            download_name=f'edited_{video_id}.mp4',
            mimetype='video/mp4'
        )
        
    except Exception as e:
        logger.error(f"❌ Download error for video_id {video_id}: {str(e)}", exc_info=True, extra={'video_id': video_id, 'request_id': g.request_id})
        return jsonify({'error': 'Video indirilirken hata oluştu'}), 500

@app.route('/api/health', methods=['GET'])
@log_execution_time()
def health_check():
    """Sağlık kontrolü endpoint'i"""
    health_status = {
        'status': 'healthy',
        'timestamp': time.time(),
        'services': {}
    }
    
    # Redis kontrolü
    try:
        if redis_client:
            redis_client.ping()
            health_status['services']['redis'] = 'connected'
            logger.debug("✅ Redis health check: OK")
        else:
            health_status['services']['redis'] = 'not configured'
            logger.warning("⚠️ Redis not configured")
    except Exception as e:
        health_status['services']['redis'] = f'error: {str(e)}'
        health_status['status'] = 'degraded'
        logger.error(f"❌ Redis health check failed: {str(e)}")
    
    # Gemini kontrolü
    health_status['services']['gemini'] = 'configured' if gemini_client else 'not configured'
    
    # Disk alanı kontrolü
    try:
        import shutil
        disk_usage = shutil.disk_usage('/')
        health_status['services']['disk'] = {
            'free_gb': round(disk_usage.free / (1024**3), 2),
            'used_percent': round((disk_usage.used / disk_usage.total) * 100, 2)
        }
        logger.debug(f"💾 Disk usage: {health_status['services']['disk']}")
    except Exception as e:
        logger.error(f"Disk check error: {str(e)}")
    
    logger.info(f"✅ Health check completed: {health_status['status']}")
    return jsonify(health_status), 200 if health_status['status'] == 'healthy' else 503

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 Starting Flask app on port {port}")
    app.run(debug=True, host='0.0.0.0', port=port)
