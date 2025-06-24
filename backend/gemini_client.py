import os
import base64
import json
import logging
from google import genai
from google.genai import types
from config import Config

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
        self.model = "gemini-2.5-flash"
        self.system_prompt = """Sen, 'Klip Asistanı' adında uzman bir video editörüsün. Görevin, kullanıcının komutlarını anlayıp sağlanan videodan kesilecek anları belirlemektir. Cevapların daima iki kısımdan oluşmalı: 1. cuts adında bir anahtar altında kesimler için geçerli bir JSON zaman damgası dizisi (örneğin: [{"start": "00:01:15", "end": "00:01:25"}]). 2. message adında bir anahtar altında kullanıcıya yönelik dostça bir mesaj. Kullanıcının komutu anlamsızsa veya video içeriğiyle alakasızsa, cuts dizisini boş bırak ve bunu message içinde kibarca belirt."""
    
    def start_conversation(self, video_path, user_prompt):
        """Yeni bir konuşma başlat"""
        try:
            # Videoyu oku ve base64'e çevir
            with open(video_path, "rb") as video_file:
                video_bytes = video_file.read()
            
            # Gemini'ye gönderilecek içeriği oluştur
            contents = [
                # Sistem Talimatı
                types.Part.from_text(self.system_prompt),
                # Kullanıcının ilk isteği: video ve metin komutu
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(
                            mime_type="video/mp4",
                            data=video_bytes
                        ),
                        types.Part.from_text(text=user_prompt),
                    ],
                ),
            ]
            
            # API'ye isteği gönder ve yanıtı al
            response = self.client.generate_content(model=self.model, contents=contents)
            
            # Yanıtı parse et ve doğrula
            parsed_response = self._parse_response(response.text)
            
            return parsed_response, contents, response.text
            
        except Exception as e:
            logger.error(f"Gemini API hatası: {str(e)}")
            return {
                "cuts": [],
                "message": "Üzgünüm, video analizinde bir hata oluştu. Lütfen tekrar deneyin."
            }, None, None
    
    def continue_conversation(self, chat_history, previous_model_response, new_user_prompt):
        """Mevcut konuşmaya devam et"""
        try:
            # Mevcut konuşma geçmişini al
            contents = chat_history
            
            # Modelin son yanıtını geçmişe ekle
            contents.append(types.Content(
                role="model",
                parts=[types.Part.from_text(previous_model_response)]
            ))
            
            # Kullanıcının yeni mesajını geçmişe ekle
            contents.append(types.Content(
                role="user",
                parts=[types.Part.from_text(new_user_prompt)]
            ))
            
            # API'ye güncellenmiş geçmişi gönder
            response = self.client.generate_content(model=self.model, contents=contents)
            
            # Yanıtı parse et ve doğrula
            parsed_response = self._parse_response(response.text)
            
            return parsed_response, contents, response.text
            
        except Exception as e:
            logger.error(f"Gemini API hatası: {str(e)}")
            return {
                "cuts": [],
                "message": "Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin."
            }, chat_history, None
    
    def _parse_response(self, response_text):
        """Gemini yanıtını parse et ve doğrula"""
        try:
            # JSON formatında yanıtı parse et
            # Önce JSON bloklarını bulmaya çalış
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            else:
                # Direkt JSON parse etmeyi dene
                json_str = response_text.strip()
            
            parsed = json.loads(json_str)
            
            # Gerekli alanları kontrol et
            if "cuts" not in parsed or "message" not in parsed:
                raise ValueError("Yanıt beklenen formatta değil")
            
            # cuts listesini doğrula
            if not isinstance(parsed["cuts"], list):
                parsed["cuts"] = []
            
            # Her kesimi doğrula
            valid_cuts = []
            for cut in parsed["cuts"]:
                if isinstance(cut, dict) and "start" in cut and "end" in cut:
                    valid_cuts.append(cut)
            
            parsed["cuts"] = valid_cuts
            
            return parsed
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Yanıt parse hatası: {str(e)}")
            # Hata durumunda varsayılan yanıt
            return {
                "cuts": [],
                "message": response_text if response_text else "Üzgünüm, yanıtı işlerken bir hata oluştu."
            }