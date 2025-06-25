import os
import base64
import json
import logging
from google import genai
from google.genai import types
from config import Config
from logging_config import LoggerMixin, log_execution_time

logger = logging.getLogger(__name__)

class GeminiClient(LoggerMixin):
    def __init__(self):
        self.log_info("Initializing Gemini client...")
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
        self.model = "gemini-2.5-flash"
        self.system_prompt = """Sen, 'Klip Asistanı' adında uzman bir video editörüsün..."""
        self.log_info(f"✅ Gemini client initialized with model: {self.model}")
    
    @log_execution_time()
    def start_conversation(self, video_path, user_prompt):
        """Yeni bir konuşma başlat"""
        self.log_info(f"Starting new conversation for video: {video_path}")
        self.log_debug(f"User prompt: {user_prompt}")
        
        try:
            # Video dosya bilgileri
            video_size = os.path.getsize(video_path)
            self.log_debug(f"Video size: {video_size} bytes")
            
            # Videoyu oku ve base64'e çevir
            self.log_debug("Reading video file...")
            with open(video_path, "rb") as video_file:
                video_bytes = video_file.read()
            
            self.log_debug(f"Video read successfully, encoding to base64...")
            
            # Gemini'ye gönderilecek içeriği oluştur
            contents = [
                types.Part.from_text(self.system_prompt),
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
            
            self.log_info("📤 Sending request to Gemini API...")
            
            # API'ye isteği gönder ve yanıtı al
            response = self.client.generate_content(model=self.model, contents=contents)
            
            self.log_info("📥 Received response from Gemini API")
            self.log_debug(f"Raw response: {response.text[:200]}...")
            
            # Yanıtı parse et ve doğrula
            parsed_response = self._parse_response(response.text)
            
            self.log_info(
                f"✅ Conversation started successfully",
                extra={
                    'cuts_count': len(parsed_response.get('cuts', [])),
                    'video_path': video_path
                }
            )
            
            return parsed_response, contents, response.text
            
        except Exception as e:
            self.log_error(f"❌ Gemini API error: {str(e)}", exc_info=True)
            return {
                "cuts": [],
                "message": "Üzgünüm, video analizinde bir hata oluştu. Lütfen tekrar deneyin."
            }, None, None
    
    def _parse_response(self, response_text):
        """Gemini yanıtını parse et ve doğrula"""
        self.log_debug("Parsing Gemini response...")
        
        try:
            # JSON formatında yanıtı parse et
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
                self.log_debug("Found JSON block in response")
            else:
                json_str = response_text.strip()
                self.log_debug("Treating entire response as JSON")
            
            parsed = json.loads(json_str)
            self.log_debug(f"Successfully parsed JSON: {list(parsed.keys())}")
            
            # Gerekli alanları kontrol et
            if "cuts" not in parsed or "message" not in parsed:
                raise ValueError("Response missing required fields")
            
            # cuts listesini doğrula
            if not isinstance(parsed["cuts"], list):
                self.log_warning("Cuts field is not a list, converting to empty list")
                parsed["cuts"] = []
            
            # Her kesimi doğrula
            valid_cuts = []
            for i, cut in enumerate(parsed["cuts"]):
                if isinstance(cut, dict) and "start" in cut and "end" in cut:
                    valid_cuts.append(cut)
                    self.log_debug(f"Valid cut {i}: {cut['start']} - {cut['end']}")
                else:
                    self.log_warning(f"Invalid cut format at index {i}: {cut}")
            
            parsed["cuts"] = valid_cuts
            self.log_info(f"✅ Response parsed successfully: {len(valid_cuts)} valid cuts")
            
            return parsed
            
        except (json.JSONDecodeError, ValueError) as e:
            self.log_error(f"❌ Response parse error: {str(e)}", exc_info=True)
            self.log_debug(f"Failed to parse response: {response_text[:500]}...")
            
            return {
                "cuts": [],
                "message": response_text if response_text else "Üzgünüm, yanıtı işlerken bir hata oluştu."
            }
