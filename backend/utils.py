import os
import uuid
import subprocess
import logging
from werkzeug.utils import secure_filename
from config import Config

logger = logging.getLogger(__name__)

def allowed_file(filename):
    """Dosya uzantısının izin verilen formatlarda olup olmadığını kontrol et"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def generate_video_id():
    """Benzersiz video ID oluştur"""
    return str(uuid.uuid4())

def get_video_duration(video_path):
    """Video süresini saniye cinsinden al"""
    try:
        cmd = [
            'ffprobe', 
            '-v', 'error', 
            '-show_entries', 'format=duration', 
            '-of', 'default=noprint_wrappers=1:nokey=1', 
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return float(result.stdout.strip())
    except Exception as e:
        logger.error(f"Video süresi alınamadı: {str(e)}")
        return 0

def timestamp_to_seconds(timestamp):
    """HH:MM:SS formatındaki zaman damgasını saniyeye çevir"""
    try:
        parts = timestamp.split(':')
        if len(parts) == 3:
            hours, minutes, seconds = map(float, parts)
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:
            minutes, seconds = map(float, parts)
            return minutes * 60 + seconds
        else:
            return float(timestamp)
    except:
        return 0

def cut_video_segment(input_path, output_path, start_time, end_time):
    """Video segmentini kes"""
    try:
        duration = timestamp_to_seconds(end_time) - timestamp_to_seconds(start_time)
        
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-ss', str(start_time),
            '-t', str(duration),
            '-c', 'copy',  # Codec'i kopyala (hızlı kesim)
            '-avoid_negative_ts', 'make_zero',
            output_path,
            '-y'  # Üzerine yaz
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"FFmpeg hatası: {result.stderr}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Video kesme hatası: {str(e)}")
        return False

def merge_video_segments(segment_paths, output_path):
    """Video segmentlerini birleştir"""
    try:
        # Geçici concat dosyası oluştur
        concat_file = f"/tmp/concat_{uuid.uuid4()}.txt"
        
        with open(concat_file, 'w') as f:
            for segment_path in segment_paths:
                f.write(f"file '{segment_path}'\n")
        
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c', 'copy',
            output_path,
            '-y'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Geçici dosyayı temizle
        if os.path.exists(concat_file):
            os.remove(concat_file)
        
        if result.returncode != 0:
            logger.error(f"FFmpeg birleştirme hatası: {result.stderr}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Video birleştirme hatası: {str(e)}")
        return False

def clean_temp_files(file_paths):
    """Geçici dosyaları temizle"""
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.error(f"Dosya silme hatası: {str(e)}")

def validate_cuts(cuts, video_duration):
    """Kesim zamanlarını doğrula"""
    valid_cuts = []
    
    for cut in cuts:
        try:
            start_seconds = timestamp_to_seconds(cut.get('start', '0'))
            end_seconds = timestamp_to_seconds(cut.get('end', '0'))
            
            # Geçerlilik kontrolleri
            if (0 <= start_seconds < end_seconds <= video_duration):
                valid_cuts.append({
                    'start': cut['start'],
                    'end': cut['end'],
                    'start_seconds': start_seconds,
                    'end_seconds': end_seconds
                })
        except Exception as e:
            logger.error(f"Kesim doğrulama hatası: {str(e)}")
            continue
    
    return valid_cuts