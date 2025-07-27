from app.models.agent_model import Language
from app.utils.logger import logger
import re
from typing import Optional

class LanguageDetector:
    """Simple language detection utility for Indian languages"""
    
    def __init__(self):
        # Simple keyword-based language detection
        self.language_keywords = {
            Language.HINDI: ['कहानी', 'व्याख्या', 'शिक्षक', 'छात्र', 'कक्षा'],
            Language.MARATHI: ['कथा', 'शिक्षक', 'विद्यार्थी', 'वर्ग', 'शेतकरी'],
            Language.GUJARATI: ['વાર્તા', 'શિક્ષક', 'વિદ્યાર્થી', 'વર્ગ'],
            Language.BENGALI: ['গল্প', 'শিক্ষক', 'ছাত্র', 'ক্লাস'],
            Language.TAMIL: ['கதை', 'ஆசிரியர்', 'மாணவர்', 'வகுப்பு'],
            Language.TELUGU: ['కథ', 'ఉపాధ్యాయుడు', 'విద్యార్థి', 'తరగతి'],
            Language.KANNADA: ['ಕಥೆ', 'ಶಿಕ್ಷಕ', 'ವಿದ್ಯಾರ್ಥಿ', 'ತರಗತಿ'],
            Language.MALAYALAM: ['കഥ', 'അധ്യാപകൻ', 'വിദ്യാർത്ഥി', 'ക്ലാസ്'],
            Language.PUNJABI: ['ਕਹਾਣੀ', 'ਅਧਿਆਪਕ', 'ਵਿਦਿਆਰਥੀ', 'ਕਲਾਸ']
        }
        
        self.english_indicators = [
            'story', 'create', 'explain', 'teacher', 'student', 'class', 
            'about', 'farmers', 'soil', 'types', 'generate'
        ]
    
    def detect_language(self, text: str) -> Language:
        """Detect language from text input"""
        try:
            text_lower = text.lower()
            
            # Check for non-English languages first
            for language, keywords in self.language_keywords.items():
                for keyword in keywords:
                    if keyword in text:
                        logger.info(f"Detected language: {language.value} based on keyword: {keyword}")
                        return language
            
            # Check for English indicators
            english_count = sum(1 for indicator in self.english_indicators if indicator in text_lower)
            if english_count > 0:
                logger.info(f"Detected language: English based on {english_count} indicators")
                return Language.ENGLISH
            
            # Default to English if no clear indicators
            logger.info("No clear language indicators found, defaulting to English")
            return Language.ENGLISH
            
        except Exception as e:
            logger.error(f"Error in language detection: {e}")
            return Language.ENGLISH

def detect_content_intent(query: str) -> dict:
    """Detect the intent and extract parameters from the query"""
    query_lower = query.lower()
    
    intent_data = {
        "content_type": "story",
        "subject": "general",
        "grade_levels": [1, 2, 3, 4, 5],
        "keywords": []
    }
    
    # Detect content type
    if any(word in query_lower for word in ['story', 'कहानी', 'कथा', 'વાર્તા']):
        intent_data["content_type"] = "story"
    elif any(word in query_lower for word in ['explain', 'explanation', 'व्याख्या']):
        intent_data["content_type"] = "explanation"
    elif any(word in query_lower for word in ['example', 'उदाहरण', 'દાખલો']):
        intent_data["content_type"] = "example"
    elif any(word in query_lower for word in ['activity', 'गतिविधि', 'પ્રવૃત્તિ']):
        intent_data["content_type"] = "activity"
    
    # Detect subject areas
    subjects = {
        'science': ['science', 'विज्ञान', 'વિજ્ઞાન', 'soil', 'water', 'plants'],
        'math': ['math', 'mathematics', 'गणित', 'ગણિત', 'numbers', 'counting'],
        'social': ['social', 'समाजिक', 'સામાજિક', 'farmers', 'community', 'history'],
        'language': ['language', 'भाषा', 'ભાષા', 'reading', 'writing', 'grammar']
    }
    
    for subject, keywords in subjects.items():
        if any(keyword in query_lower for keyword in keywords):
            intent_data["subject"] = subject
            break
    
    # Extract grade information
    grade_patterns = [
        r'grade\s*(\d+)',
        r'class\s*(\d+)',
        r'कक्षा\s*(\d+)',
        r'વર્ગ\s*(\d+)'
    ]
    
    for pattern in grade_patterns:
        matches = re.findall(pattern, query_lower)
        if matches:
            intent_data["grade_levels"] = [int(match) for match in matches]
            break
    
    return intent_data


def is_language_supported(language: str) -> bool:
    """Check if the language is supported."""
    supported_languages = ["english", "hindi", "gujarati", "marathi", "telugu", "tamil", "kannada", 
                           "bengali", "punjabi", "urdu", "malayalam", "odia"]
    return language.lower() in supported_languages


def detect_language(text: str) -> str:
    """
    Detect the language of the given text using Google Cloud Translation API.
    
    Args:
        text: The text to detect the language of
        
    Returns:
        The detected language name (e.g., "English", "Hindi", etc.)
    """
    try:
        # Try to use Google Cloud Translation API if available
        from google.cloud import translate_v2 as translate
        
        client = translate.Client()
        result = client.detect_language(text[:500])  # Use first 500 chars for efficiency
        
        # Map language codes to full names
        language_map = {
            "en": "English",
            "hi": "Hindi",
            "gu": "Gujarati",
            "mr": "Marathi",
            "te": "Telugu",
            "ta": "Tamil",
            "kn": "Kannada",
            "bn": "Bengali",
            "pa": "Punjabi",
            "ur": "Urdu",
            "ml": "Malayalam",
            "or": "Odia"
        }
        
        detected = language_map.get(result["language"], "English")
        logger.info(f"Detected language: {detected} with confidence {result['confidence']}")
        return detected
        
    except Exception as e:
        logger.warning(f"Error detecting language: {e}. Defaulting to English.")
        return "English"


def translate_text(text: str, target_language: str) -> str:
    """
    Translate text to the target language using Google Cloud Translation API.
    
    Args:
        text: The text to translate
        target_language: The target language to translate to
        
    Returns:
        The translated text
    """
    try:
        if target_language.lower() == "english":
            return text
            
        # Try to use Google Cloud Translation API if available
        from google.cloud import translate_v2 as translate
        
        # Map common language names to language codes
        language_code_map = {
            "english": "en",
            "hindi": "hi",
            "gujarati": "gu",
            "marathi": "mr",
            "telugu": "te",
            "tamil": "ta",
            "kannada": "kn",
            "bengali": "bn",
            "punjabi": "pa",
            "urdu": "ur",
            "malayalam": "ml",
            "odia": "or"
        }
        
        # Get language code
        target_code = language_code_map.get(target_language.lower(), target_language)
        
        # Translate text
        client = translate.Client()
        result = client.translate(text, target_language=target_code)
        
        translated_text = result["translatedText"]
        logger.info(f"Successfully translated text to {target_language}")
        
        return translated_text
        
    except Exception as e:
        logger.error(f"Error translating text: {e}")
        return text  # Return original text if translation fails
