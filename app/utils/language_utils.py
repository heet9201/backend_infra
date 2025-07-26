from app.models.agent_model import Language
from app.utils.logger import logger
import re

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
