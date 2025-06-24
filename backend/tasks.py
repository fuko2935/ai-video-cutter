import os
import json
import redis
import logging
from celery import Task
from celery_app import celery_app
from config import Config
from utils import (
    get_video_duration, cut_video_segment, 
    merge_video_segments, clean_temp_files, validate_cuts
)

logger = logging.getLogger(__name__)
redis_client = redis.from_url(Config.REDIS_URL)

class VideoTask(Task):
    """Video işleme görevleri için temel sınıf"""
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Görev başarısız olduğunda"""
        video_id = args[0] if args else kwargs.get('video_id')
        if video_id:
            self._update_status(video_id, 'error', str(exc))
    
    def _update_status(self, video_id, status, message=''):
        """Video işleme durumunu güncelle"""
        status_data = {
            'status': status,
            'message': message
        }
        redis_client.setex(
            f'video_status:{video_id}',
            3600,  # 1 saat
            json.dumps(status_data)
        )

@celery_app.task(base=VideoTask, bind=True)
def process_video_upload(self, video_id, video_path):
    """Video yükleme sonrası işlemleri yap"""
    try:
        # Durumu güncelle
        self._update_status(video_id, 'processing', 'Video analiz ediliyor...')
        
        # Video süresini al
        duration = get_video_duration(video_path)
        
        if duration == 0:
            raise ValueError("Video süresi alınamadı")
        
        # Video bilgilerini Redis'e kaydet
        video_info = {
            'id': video_id,
            'path': video_path,
            'duration': duration,
            'status': 'ready'
        }
        
        redis_client.setex(
            f'video_info:{video_id}',
            3600,  # 1 saat
            json.dumps(video_info)
        )
        
        # Durumu güncelle
        self._update_status(video_id, 'ready', 'Video analiz için hazır')
        
        return {
            'video_id': video_id,
            'duration': duration,
            'status': 'ready'
        }
        
    except Exception as e:
        logger.error(f"Video işleme hatası: {str(e)}")
        self._update_status(video_id, 'error', str(e))
        raise

@celery_app.task(base=VideoTask, bind=True)
def finalize_video(self, video_id, cuts):
    """Kesim listesine göre nihai videoyu oluştur"""
    try:
        # Durumu güncelle
        self._update_status(video_id, 'processing', 'Video kesiliyor...')
        
        # Video bilgilerini al
        video_info_str = redis_client.get(f'video_info:{video_id}')
        if not video_info_str:
            raise ValueError("Video bilgileri bulunamadı")
        
        video_info = json.loads(video_info_str)
        video_path = video_info['path']
        video_duration = video_info['duration']
        
        # Kesimleri doğrula
        valid_cuts = validate_cuts(cuts, video_duration)
        
        if not valid_cuts:
            raise ValueError("Geçerli kesim bulunamadı")
        
        # Her kesim için segment oluştur
        segment_paths = []
        temp_files = []
        
        for i, cut in enumerate(valid_cuts):
            segment_path = os.path.join(
                Config.PROCESSED_FOLDER,
                f"{video_id}_segment_{i}.mp4"
            )
            
            success = cut_video_segment(
                video_path,
                segment_path,
                cut['start'],
                cut['end']
            )
            
            if success:
                segment_paths.append(segment_path)
                temp_files.append(segment_path)
            else:
                # Hata durumunda temizlik yap
                clean_temp_files(temp_files)
                raise ValueError(f"Segment {i} kesilemedi")
        
        # Durumu güncelle
        self._update_status(video_id, 'processing', 'Segmentler birleştiriliyor...')
        
        # Segmentleri birleştir
        output_path = os.path.join(
            Config.PROCESSED_FOLDER,
            f"{video_id}_final.mp4"
        )
        
        success = merge_video_segments(segment_paths, output_path)
        
        # Geçici segmentleri temizle
        clean_temp_files(temp_files)
        
        if not success:
            raise ValueError("Video birleştirilemedi")
        
        # Sonuç bilgilerini Redis'e kaydet
        result_info = {
            'video_id': video_id,
            'output_path': output_path,
            'cuts_count': len(valid_cuts),
            'status': 'completed'
        }
        
        redis_client.setex(
            f'video_result:{video_id}',
            3600,  # 1 saat
            json.dumps(result_info)
        )
        
        # Durumu güncelle
        self._update_status(video_id, 'completed', 'Video hazır!')
        
        return result_info
        
    except Exception as e:
        logger.error(f"Video birleştirme hatası: {str(e)}")
        self._update_status(video_id, 'error', str(e))
        raise

@celery_app.task
def cleanup_old_files():
    """Eski dosyaları temizle (günlük çalışacak)"""
    try:
        import time
        current_time = time.time()
        
        # Upload ve processed klasörlerini temizle
        for folder in [Config.UPLOAD_FOLDER, Config.PROCESSED_FOLDER]:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                
                # 24 saatten eski dosyaları sil
                if os.path.getmtime(file_path) < current_time - 86400:
                    try:
                        os.remove(file_path)
                        logger.info(f"Eski dosya silindi: {file_path}")
                    except Exception as e:
                        logger.error(f"Dosya silme hatası: {str(e)}")
                        
    except Exception as e:
        logger.error(f"Temizlik hatası: {str(e)}")