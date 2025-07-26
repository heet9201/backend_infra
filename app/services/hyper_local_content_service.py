from app.models.agent_model import (
    HyperLocalContentRequest, AgentResponse, AgentType, Language, ContentType
)
from app.core.vertex_ai import generate_educational_content
from app.utils.logger import logger
from typing import Dict, Any

class HyperLocalContentService:
    """Service for generating hyper-local, culturally relevant educational content"""
    
    def __init__(self):
        self.language_contexts = {
            Language.HINDI: "Hindi-speaking regions of North India",
            Language.MARATHI: "Maharashtra state with rural farming communities",
            Language.GUJARATI: "Gujarat state with diverse agricultural and business communities",
            Language.BENGALI: "West Bengal and Bangladesh regions with rich cultural heritage",
            Language.TAMIL: "Tamil Nadu with strong literary and cultural traditions",
            Language.TELUGU: "Andhra Pradesh and Telangana regions",
            Language.KANNADA: "Karnataka state with diverse geographical features",
            Language.MALAYALAM: "Kerala state with high literacy and unique geography",
            Language.PUNJABI: "Punjab region with agricultural prominence",
            Language.ENGLISH: "Pan-Indian context with local examples"
        }
        
        self.content_templates = {
            ContentType.STORY: self._generate_story_prompt,
            ContentType.EXPLANATION: self._generate_explanation_prompt,
            ContentType.EXAMPLE: self._generate_example_prompt,
            ContentType.ACTIVITY: self._generate_activity_prompt
        }
    
    def generate_content(self, request: HyperLocalContentRequest) -> AgentResponse:
        """Generate hyper-local educational content based on the request"""
        try:
            # Get the appropriate prompt template
            prompt_generator = self.content_templates.get(
                request.content_type, 
                self._generate_story_prompt
            )
            
            # Generate the prompt
            prompt = prompt_generator(request)
            
            # Generate content using Vertex AI
            response_text = generate_educational_content(prompt, request.language.value)
            
            return AgentResponse(
                status="success",
                agent_type=AgentType.HYPER_LOCAL_CONTENT,
                response=response_text,
                language=request.language,
                metadata={
                    "topic": request.topic,
                    "content_type": request.content_type.value,
                    "grade_levels": request.grade_levels,
                    "cultural_context": request.cultural_context
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating hyper-local content: {e}")
            return AgentResponse(
                status="error",
                agent_type=AgentType.HYPER_LOCAL_CONTENT,
                response=f"I apologize, but I couldn't generate the requested content about {request.topic}. Please try rephrasing your request.",
                language=request.language,
                error_message=str(e)
            )
    
    def _generate_story_prompt(self, request: HyperLocalContentRequest) -> str:
        """Generate prompt for story creation"""
        cultural_context = self.language_contexts.get(
            request.language, 
            "Indian rural context"
        )
        
        return f"""Create an engaging educational story in {request.language.value} about {request.topic}.

Context and Requirements:
- Setting: {cultural_context}
- Target grades: {', '.join(map(str, request.grade_levels))}
- Cultural context: {request.cultural_context}
- Subject: {request.subject or 'general education'}

Story Guidelines:
1. Use simple, age-appropriate language suitable for grades {min(request.grade_levels)}-{max(request.grade_levels)}
2. Include local characters with Indian names
3. Set the story in a familiar Indian context (village, small town, or familiar urban setting)
4. Incorporate the educational concept naturally into the narrative
5. Use cultural references that Indian students can relate to
6. Make it engaging and memorable for children
7. Include moral or practical lessons
8. Keep the story length appropriate for classroom storytelling (3-5 minutes)

Additional requirements: {request.additional_requirements or 'None'}

Please create a complete story that teachers can easily read aloud and use to explain {request.topic} to their students."""
    
    def _generate_explanation_prompt(self, request: HyperLocalContentRequest) -> str:
        """Generate prompt for educational explanations"""
        cultural_context = self.language_contexts.get(
            request.language, 
            "Indian context"
        )
        
        return f"""Provide a clear, simple explanation of {request.topic} in {request.language.value}.

Context:
- Audience: Students in grades {', '.join(map(str, request.grade_levels))}
- Cultural setting: {cultural_context}
- Teaching context: {request.cultural_context}

Explanation Requirements:
1. Use simple vocabulary appropriate for the grade levels
2. Include examples from everyday Indian life
3. Use analogies that Indian children can understand
4. Break down complex concepts into smaller parts
5. Provide practical examples or demonstrations teachers can use
6. Include local references and familiar objects/situations
7. Make it interactive with questions teachers can ask students

Additional context: {request.additional_requirements or 'None'}

Please provide a comprehensive yet simple explanation that teachers can use in multi-grade classrooms."""
    
    def _generate_example_prompt(self, request: HyperLocalContentRequest) -> str:
        """Generate prompt for practical examples"""
        return f"""Provide practical, relatable examples to explain {request.topic} in {request.language.value}.

Requirements:
- Target grades: {', '.join(map(str, request.grade_levels))}
- Cultural context: {request.cultural_context}
- Use examples from Indian daily life, agriculture, festivals, or local customs
- Make examples visual and hands-on where possible
- Include multiple examples for different grade levels
- Ensure examples are relevant to rural and semi-urban Indian contexts

Additional requirements: {request.additional_requirements or 'None'}

Please provide 3-5 practical examples that teachers can use to illustrate {request.topic}."""
    
    def _generate_activity_prompt(self, request: HyperLocalContentRequest) -> str:
        """Generate prompt for educational activities"""
        return f"""Design engaging classroom activities to teach {request.topic} in {request.language.value}.

Activity Requirements:
- Suitable for grades {', '.join(map(str, request.grade_levels))}
- Can be conducted in resource-limited classrooms
- Use materials commonly available in Indian schools
- Suitable for multi-grade teaching
- Culturally relevant to {request.cultural_context}
- Interactive and hands-on where possible

Please provide:
1. 2-3 different activities for different learning styles
2. Clear step-by-step instructions for teachers
3. List of required materials (keep it simple and accessible)
4. Learning outcomes for each activity
5. Assessment suggestions

Additional requirements: {request.additional_requirements or 'None'}

Design activities that will help students understand {request.topic} through practical engagement."""
