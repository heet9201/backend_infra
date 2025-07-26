from app.models.agent_model import (
    HyperLocalContentRequest, AgentResponse, AgentType, Language, ContentType, SessionInfo,
    HyperLocalContentResponse, ContentPiece, Subject
)
from app.core.vertex_ai import generate_educational_content
from app.utils.logger import logger
from app.services.session_service import session_service
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import re

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
            ContentType.STORIES_NARRATIVES: self._generate_story_prompt,
            ContentType.WORD_PROBLEMS: self._generate_word_problems_prompt,
            ContentType.READING_COMPREHENSION: self._generate_reading_comprehension_prompt,
            ContentType.ACTIVITY_INSTRUCTIONS: self._generate_activity_instructions_prompt,
            ContentType.STORY: self._generate_story_prompt,
            ContentType.EXPLANATION: self._generate_explanation_prompt,
            ContentType.EXAMPLE: self._generate_example_prompt,
            ContentType.ACTIVITY: self._generate_activity_prompt,
            ContentType.WORKSHEET: self._generate_worksheet_prompt,
            ContentType.LESSON_PLAN: self._generate_lesson_plan_prompt
        }
        
        # Location-specific cultural elements
        self.location_cultural_elements = {
            "mumbai": ["local trains", "dabbawalas", "vada pav", "ganesh festival"],
            "delhi": ["red fort", "metro", "street food", "diwali celebrations"],
            "bangalore": ["gardens", "it culture", "filter coffee", "mysore pak"],
            "kolkata": ["trams", "fish market", "durga puja", "rosogolla"],
            "chennai": ["marina beach", "temple festivals", "filter coffee", "classical music"],
            "pune": ["hills", "it companies", "misal pav", "ganesh festival"],
            "hyderabad": ["charminar", "biryani", "tech city", "bonalu festival"],
            "ahmedabad": ["textiles", "garba dance", "thali", "kite festival"]
        }
        
        # Regional currencies and units
        self.regional_context = {
            "currency": "रुपये (Rupees)",
            "measurement_units": {
                "land": ["एकड़ (Acre)", "बीघा (Bigha)", "हेक्टेयर (Hectare)"],
                "weight": ["किलो (Kilo)", "क्विंटल (Quintal)", "टन (Ton)"],
                "distance": ["किलोमीटर (Kilometer)", "मीटर (Meter)"]
            }
        }
    
    def generate_content(self, request: HyperLocalContentRequest, user_id: Optional[str] = None) -> HyperLocalContentResponse:
        """Generate enhanced hyper-local educational content based on the request"""
        start_time = datetime.now()
        
        try:
            # Handle session if user_id is provided
            if user_id:
                # Get or create session for the user
                user_session = session_service.get_session(user_id)
                
                # Update session with language preference
                user_session.language_preference = request.language.value
                
                # Add the user request to session history
                session_service.add_message(
                    user_id=user_id,
                    content=f"Generate {request.content_type.value} about {request.topic} for grade {request.grade_levels}",
                    agent_type="user",
                    metadata={
                        "language": request.language.value,
                        "topic": request.topic,
                        "content_type": request.content_type.value,
                        "subject": request.subject.value,
                        "location": request.location
                    }
                )
            
            # Generate content pieces
            content_pieces = []
            cultural_elements_used = []
            local_references = []
            dialect_terms = {}
            
            # Determine number of content pieces to generate
            piece_count = request.preview_count if request.generate_preview else 1
            
            for i in range(piece_count):
                # Get the appropriate prompt template
                prompt_generator = self.content_templates.get(
                    request.content_type, 
                    self._generate_story_prompt
                )
                
                # Generate the prompt with enhanced context
                prompt = prompt_generator(request, piece_index=i)
                
                # Generate content using Vertex AI
                response_text = generate_educational_content(prompt, request.language.value)
                
                # Extract local elements and cultural annotations
                local_elements, cultural_annotations = self._extract_cultural_elements(
                    response_text, request.location, request.language
                )
                
                # Create content piece
                content_piece = ContentPiece(
                    title=f"{request.topic} - {request.content_type.value.title()} {i+1}",
                    content=response_text,
                    content_type=request.content_type,
                    local_elements=local_elements,
                    cultural_annotations=cultural_annotations,
                    difficulty_level=request.difficulty_level,
                    estimated_time=self._estimate_content_time(response_text, request.content_type)
                )
                
                content_pieces.append(content_piece)
                cultural_elements_used.extend(local_elements)
                local_references.extend(self._extract_local_references(response_text, request.location))
                
                # Extract dialect terms if enabled
                if request.include_local_dialect:
                    dialect_terms.update(self._extract_dialect_terms(response_text, request.language))
            
            # Generate questions if requested
            questions = []
            if request.include_questions and request.question_types:
                questions = self._generate_questions(request, content_pieces[0].content)
            
            # Calculate generation time and quality score
            generation_time = str(datetime.now() - start_time)
            quality_score = self._calculate_quality_score(content_pieces, request)
            
            # Create enhanced response object
            response = HyperLocalContentResponse(
                status="success",
                agent_type=AgentType.HYPER_LOCAL_CONTENT,
                language=request.language,
                location=request.location,
                subject=request.subject.value,
                grade_levels=request.grade_levels,
                content_pieces=content_pieces,
                questions=questions,
                cultural_elements_used=list(set(cultural_elements_used)),
                local_references=list(set(local_references)),
                dialect_terms=dialect_terms,
                generation_time=generation_time,
                content_quality_score=quality_score,
                metadata={
                    "topic": request.topic,
                    "content_type": request.content_type.value,
                    "difficulty_level": request.difficulty_level,
                    "include_local_examples": request.include_local_examples,
                    "include_cultural_context": request.include_cultural_context,
                    "piece_count": len(content_pieces)
                }
            )
            
            # Add agent response to session if user_id is provided
            if user_id:
                user_session = session_service.get_session(user_id)
                session_service.add_message(
                    user_id=user_id,
                    content=f"Generated {len(content_pieces)} {request.content_type.value} pieces about {request.topic}",
                    agent_type=AgentType.HYPER_LOCAL_CONTENT.value,
                    metadata={
                        "language": request.language.value,
                        "topic": request.topic,
                        "content_type": request.content_type.value,
                        "status": "success",
                        "piece_count": len(content_pieces),
                        "quality_score": quality_score
                    }
                )
                
                # Add session information to the response
                response.session = SessionInfo(
                    session_id=user_session.session_id,
                    user_id=user_session.user_id,
                    language_preference=user_session.language_preference,
                    message_count=len(user_session.messages),
                    context_keys=list(user_session.context.keys()) if user_session.context else [],
                    last_active=user_session.last_active.isoformat() if isinstance(user_session.last_active, datetime) else str(user_session.last_active)
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating hyper-local content: {e}")
            error_response = HyperLocalContentResponse(
                status="error",
                agent_type=AgentType.HYPER_LOCAL_CONTENT,
                language=request.language,
                location=request.location,
                subject=request.subject.value if hasattr(request, 'subject') else "general",
                grade_levels=request.grade_levels,
                content_pieces=[],
                error_message=str(e),
                generation_time=str(datetime.now() - start_time)
            )
            
            # Add error response to session if user_id is provided
            if user_id:
                try:
                    user_session = session_service.get_session(user_id)
                    session_service.add_message(
                        user_id=user_id,
                        content=f"Error generating content for {request.topic}: {str(e)}",
                        agent_type=AgentType.HYPER_LOCAL_CONTENT.value,
                        metadata={
                            "status": "error",
                            "error_message": str(e)
                        }
                    )
                    
                    # Add session information to the error response
                    error_response.session = SessionInfo(
                        session_id=user_session.session_id,
                        user_id=user_session.user_id,
                        language_preference=user_session.language_preference,
                        message_count=len(user_session.messages),
                        context_keys=list(user_session.context.keys()) if user_session.context else [],
                        last_active=user_session.last_active.isoformat() if isinstance(user_session.last_active, datetime) else str(user_session.last_active)
                    )
                except Exception as session_error:
                    logger.error(f"Error updating session during error handling: {session_error}")
                
            return error_response
    
    def _get_cultural_context(self, location: Optional[str], culture: Optional[str]) -> str:
        """Get cultural context for content generation"""
        cultural_context = ""
        
        if location and location.lower() in self.location_cultural_elements:
            elements = self.location_cultural_elements[location.lower()]
            cultural_context = f"Local elements from {location}: {', '.join(elements[:3])}"
        
        if culture:
            cultural_context += f". Cultural setting: {culture}"
        
        return cultural_context or "General Indian cultural context"
    
    def _extract_cultural_elements(self, content: str, location: Optional[str], language: Language) -> tuple:
        """Extract local elements and cultural annotations from content"""
        local_elements = []
        cultural_annotations = []
        
        # Extract location-specific elements
        if location and location.lower() in self.location_cultural_elements:
            for element in self.location_cultural_elements[location.lower()]:
                if element.lower() in content.lower():
                    local_elements.append(element)
        
        # Extract cultural annotations based on patterns
        # Look for Indian names, festivals, currency mentions, etc.
        patterns = {
            "Indian names": r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',
            "Currency": r'रुपये|rupees|₹',
            "Festivals": r'दिवाली|होली|ईद|दुर्गा पूजा|गणेश चतुर्थी|diwali|holi|eid|durga puja',
            "Local units": r'बीघा|एकड़|क्विंटल|bigha|acre|quintal'
        }
        
        for category, pattern in patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                cultural_annotations.append(f"{category}: {', '.join(set(matches))}")
        
        return local_elements[:5], cultural_annotations[:3]  # Limit to avoid clutter
    
    def _extract_local_references(self, content: str, location: Optional[str]) -> List[str]:
        """Extract local geographical and cultural references"""
        references = []
        
        # Common Indian geographical terms
        geo_patterns = [
            r'गाँव|village', r'शहर|city', r'बाजार|market', r'नदी|river',
            r'पहाड़|mountain', r'खेत|farm', r'स्कूल|school'
        ]
        
        for pattern in geo_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            references.extend([match for match in matches if match not in references])
        
        return references[:5]  # Limit to avoid clutter
    
    def _extract_dialect_terms(self, content: str, language: Language) -> Dict[str, str]:
        """Extract and provide meanings for dialect terms"""
        dialect_terms = {}
        
        # Sample dialect terms with meanings (can be expanded)
        dialect_mappings = {
            Language.HINDI: {
                "बीघा": "स्थानीय भूमि माप इकाई (Local land measurement unit)",
                "क्विंटल": "100 किलो का माप (100 kg measurement)",
                "पंचायत": "गाँव की स्थानीय सरकार (Village local government)"
            },
            Language.MARATHI: {
                "साडी": "Traditional Indian garment",
                "मोर": "Peacock - state bird of Maharashtra",
                "वडापाव": "Popular street food in Maharashtra"
            }
        }
        
        if language in dialect_mappings:
            for term, meaning in dialect_mappings[language].items():
                if term in content:
                    dialect_terms[term] = meaning
        
        return dialect_terms
    
    def _estimate_content_time(self, content: str, content_type: ContentType) -> str:
        """Estimate time to read/complete content"""
        word_count = len(content.split())
        
        time_mappings = {
            ContentType.STORIES_NARRATIVES: f"{max(2, word_count // 100)} minutes reading",
            ContentType.READING_COMPREHENSION: f"{max(3, word_count // 80)} minutes reading + questions",
            ContentType.WORD_PROBLEMS: f"{max(5, word_count // 50)} minutes solving",
            ContentType.ACTIVITY_INSTRUCTIONS: f"{max(10, word_count // 30)} minutes activity",
            ContentType.WORKSHEET: f"{max(15, word_count // 25)} minutes completion"
        }
        
        return time_mappings.get(content_type, f"{max(2, word_count // 100)} minutes")
    
    def _generate_questions(self, request: HyperLocalContentRequest, content: str) -> List[Dict[str, Any]]:
        """Generate assessment questions based on content"""
        questions = []
        
        for question_type in request.question_types:
            if question_type == "mcq":
                # Generate multiple choice questions
                question_prompt = f"""Based on this content about {request.topic}, create 2 multiple choice questions in {request.language.value} suitable for grade {request.grade_levels}.

Content: {content[:500]}...

Format each question as:
Question: [question text]
A) [option 1]
B) [option 2] 
C) [option 3]
D) [option 4]
Correct Answer: [letter]
"""
                
                try:
                    mcq_response = generate_educational_content(question_prompt, request.language.value)
                    questions.append({
                        "type": "mcq",
                        "content": mcq_response,
                        "subject": request.subject.value,
                        "grade_levels": request.grade_levels
                    })
                except Exception as e:
                    logger.error(f"Error generating MCQ: {e}")
            
            elif question_type == "short_answer":
                # Generate short answer questions
                questions.append({
                    "type": "short_answer",
                    "content": f"समझाइए कि {request.topic} आपके दैनिक जीवन में कैसे उपयोगी है? (Explain how {request.topic} is useful in your daily life?)",
                    "subject": request.subject.value,
                    "grade_levels": request.grade_levels
                })
        
        return questions[:3]  # Limit to 3 questions
    
    def _calculate_quality_score(self, content_pieces: List[ContentPiece], request: HyperLocalContentRequest) -> float:
        """Calculate a quality score for the generated content"""
        score = 0.0
        total_factors = 0
        
        for piece in content_pieces:
            # Check for local elements
            if piece.local_elements:
                score += 0.2
            total_factors += 0.2
            
            # Check for cultural annotations
            if piece.cultural_annotations:
                score += 0.15
            total_factors += 0.15
            
            # Check content length appropriateness
            word_count = len(piece.content.split())
            if 50 <= word_count <= 500:  # Appropriate length
                score += 0.25
            total_factors += 0.25
            
            # Check for grade-appropriate language (simplified check)
            avg_word_length = sum(len(word) for word in piece.content.split()) / max(word_count, 1)
            if request.grade_levels and max(request.grade_levels) <= 5 and avg_word_length <= 6:
                score += 0.2
            elif request.grade_levels and max(request.grade_levels) > 5 and avg_word_length <= 8:
                score += 0.2
            total_factors += 0.2
            
            # Check for topic relevance (basic keyword matching)
            if request.topic.lower() in piece.content.lower():
                score += 0.2
            total_factors += 0.2
        
        return round(score / max(total_factors, 1) * 100, 2)  # Return as percentage
    
    def _generate_story_prompt(self, request: HyperLocalContentRequest, piece_index: int = 0) -> str:
        """Generate enhanced prompt for story creation"""
        cultural_context = self.language_contexts.get(
            request.language, 
            "Indian rural context"
        )
        
        # Get location-specific elements
        location_elements = ""
        if request.location and request.location.lower() in self.location_cultural_elements:
            elements = self.location_cultural_elements[request.location.lower()]
            location_elements = f"Local elements to include: {', '.join(elements[:3])}"
        
        # Build cultural requirements
        cultural_requirements = []
        if request.include_local_examples:
            cultural_requirements.append("Include local examples and references")
        if request.include_cultural_context:
            cultural_requirements.append("Incorporate cultural traditions and festivals")
        if request.include_local_currency:
            cultural_requirements.append("Use Indian currency (रुपये/Rupees) in examples")
        if request.include_local_dialect:
            cultural_requirements.append("Include regional words with explanations")
        
        prompt = f"""Create an engaging educational story in {request.language.value} about {request.topic} for {request.subject.value}.

Context and Requirements:
- Setting: {cultural_context} - {request.location or "Indian context"}
- Target grades: {', '.join(map(str, request.grade_levels))}
- Cultural context: {request.cultural_context}
- Subject: {request.subject.value}
- Difficulty level: {request.difficulty_level}

{location_elements}

Story Guidelines:
1. Use simple, age-appropriate language suitable for grades {min(request.grade_levels)}-{max(request.grade_levels)}
2. Include local characters with Indian names appropriate to {request.location or "the region"}
3. Set the story in a familiar Indian context (village, small town, or urban setting)
4. Incorporate the educational concept naturally into the narrative
5. Use cultural references that Indian students can relate to
6. Make it engaging and memorable for children
7. Include moral or practical lessons
8. Keep the story length appropriate for classroom storytelling

Cultural Requirements:
{chr(10).join(f"- {req}" for req in cultural_requirements)}

Additional requirements: {request.additional_requirements or 'Make it relatable to local students'}

Please create a complete story (variant {piece_index + 1}) that teachers can easily read aloud and use to explain {request.topic} to their students. Include cultural elements naturally in the narrative."""
        
        return prompt

    def _generate_explanation_prompt(self, request: HyperLocalContentRequest, piece_index: int = 0) -> str:
        """Generate prompt for educational explanations"""
        cultural_context = self._get_cultural_context(request.location, request.culture)
        
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

    def _generate_example_prompt(self, request: HyperLocalContentRequest, piece_index: int = 0) -> str:
        """Generate prompt for practical examples"""
        cultural_context = self._get_cultural_context(request.location, request.culture)
        
        return f"""Provide practical, relatable examples to explain {request.topic} in {request.language.value}.

Requirements:
- Target grades: {', '.join(map(str, request.grade_levels))}
- Cultural context: {cultural_context}
- Use examples from Indian daily life, agriculture, festivals, or local customs
- Make examples visual and hands-on where possible
- Include multiple examples for different grade levels
- Ensure examples are relevant to rural and semi-urban Indian contexts

Additional requirements: {request.additional_requirements or 'None'}

Please provide 3-5 practical examples that teachers can use to illustrate {request.topic}."""

    def _generate_activity_prompt(self, request: HyperLocalContentRequest, piece_index: int = 0) -> str:
        """Generate prompt for educational activities"""
        cultural_context = self._get_cultural_context(request.location, request.culture)
        
        return f"""Design engaging classroom activities to teach {request.topic} in {request.language.value}.

Activity Requirements:
- Suitable for grades {', '.join(map(str, request.grade_levels))}
- Can be conducted in resource-limited classrooms
- Use materials commonly available in Indian schools
- Suitable for multi-grade teaching
- Culturally relevant to {cultural_context}
- Interactive and hands-on where possible

Please provide:
1. 2-3 different activities for different learning styles
2. Clear step-by-step instructions for teachers
3. List of required materials (keep it simple and accessible)
4. Learning outcomes for each activity
5. Assessment suggestions

Additional requirements: {request.additional_requirements or 'None'}

Design activities that will help students understand {request.topic} through practical engagement."""

    def _generate_word_problems_prompt(self, request: HyperLocalContentRequest, piece_index: int = 0) -> str:
        """Generate prompt for creating word problems with local context."""
        cultural_context = self._get_cultural_context(request.location, request.culture)
        
        return f"""Create {request.variations} word problems for {request.subject} on the topic '{request.topic}' suitable for {request.grade_levels} students.

Location Context: {request.location}
Cultural Elements: {cultural_context}
Difficulty Level: {request.difficulty_level}
Language: {request.language}

Requirements:
1. Use local names, places, and cultural references from {request.location}
2. Include practical scenarios students can relate to
3. Vary difficulty within the {request.difficulty_level} range
4. Provide step-by-step solutions
5. Include real-world applications

Problem Structure:
- Clear problem statement with local context
- Relevant data/numbers
- Question that tests {request.topic} concepts
- Solution with explanation

Additional requirements: {request.additional_requirements or 'None'}

Make the problems engaging and culturally relevant."""

    def _generate_reading_comprehension_prompt(self, request: HyperLocalContentRequest, piece_index: int = 0) -> str:
        """Generate prompt for creating reading comprehension passages."""
        cultural_context = self._get_cultural_context(request.location, request.culture)
        
        return f"""Create a reading comprehension passage about '{request.topic}' for {request.grade_levels} students.

Location Context: {request.location}
Cultural Elements: {cultural_context}
Difficulty Level: {request.difficulty_level}
Language: {request.language}

Requirements:
1. 200-400 word passage (adjust for grade level)
2. Use vocabulary appropriate for {request.grade_levels}
3. Include local references and cultural context from {request.location}
4. Create 5-8 comprehension questions of varying difficulty
5. Include questions testing: literal understanding, inference, vocabulary, main idea

Question Types:
- Multiple choice (2-3 questions)
- Short answer (2-3 questions)
- One detailed response question

Passage Theme: Focus on {request.topic} while incorporating local culture and context.

Additional requirements: {request.additional_requirements or 'None'}

Make the content engaging and culturally relevant."""

    def _generate_activity_instructions_prompt(self, request: HyperLocalContentRequest, piece_index: int = 0) -> str:
        """Generate prompt for creating detailed activity instructions."""
        cultural_context = self._get_cultural_context(request.location, request.culture)
        
        return f"""Create detailed activity instructions for teaching '{request.topic}' to {request.grade_levels} students.

Location Context: {request.location}
Cultural Elements: {cultural_context}
Difficulty Level: {request.difficulty_level}
Language: {request.language}

Requirements:
1. 3-4 different activities for different learning styles
2. Clear step-by-step instructions
3. List of required materials (locally available)
4. Time estimates for each activity
5. Learning objectives
6. Assessment rubric

Activity Types to Include:
- Hands-on/practical activity
- Group discussion/collaboration
- Individual reflection/practice
- Creative expression (drawing, writing, etc.)

For each activity provide:
- Title and objective
- Materials needed
- Step-by-step procedure
- Expected outcomes
- Assessment criteria

Additional requirements: {request.additional_requirements or 'None'}

Incorporate local culture and make activities practical and engaging."""

    def _generate_worksheet_prompt(self, request: HyperLocalContentRequest, piece_index: int = 0) -> str:
        """Generate prompt for creating worksheets with local context."""
        cultural_context = self._get_cultural_context(request.location, request.culture)
        
        return f"""Create a comprehensive worksheet on '{request.topic}' for {request.grade_levels} students.

Location Context: {request.location}
Cultural Elements: {cultural_context}
Difficulty Level: {request.difficulty_level}
Language: {request.language}

Worksheet Requirements:
1. Title and learning objectives
2. 10-15 questions of varying difficulty
3. Mix of question types: multiple choice, fill-in-blanks, short answer, problem-solving
4. Include local examples and cultural references
5. Answer key with explanations
6. Extension activities for advanced learners

Question Categories:
- Basic concept understanding (30%)
- Application problems (40%)
- Analysis/critical thinking (20%)
- Creative/open-ended (10%)

Format:
- Clear instructions for each section
- Appropriate spacing for student responses
- Visual elements where helpful
- Progressive difficulty

Additional requirements: {request.additional_requirements or 'None'}

Make the worksheet engaging with local context and real-world applications."""

    def _generate_lesson_plan_prompt(self, request: HyperLocalContentRequest, piece_index: int = 0) -> str:
        """Generate prompt for creating detailed lesson plans."""
        cultural_context = self._get_cultural_context(request.location, request.culture)
        
        return f"""Create a detailed lesson plan for teaching '{request.topic}' to {request.grade_levels} students.

Location Context: {request.location}
Cultural Elements: {cultural_context}
Difficulty Level: {request.difficulty_level}
Language: {request.language}
Duration: 45-60 minutes

Lesson Plan Structure:
1. Title and Subject
2. Learning Objectives (3-4 specific, measurable goals)
3. Prerequisites/Prior Knowledge
4. Materials Required
5. Lesson Introduction (5-10 minutes)
6. Main Content Delivery (20-30 minutes)
7. Activities and Practice (10-15 minutes)
8. Conclusion and Assessment (5-10 minutes)
9. Homework/Extension Activities
10. Assessment Rubric

Key Requirements:
- Incorporate local culture and examples from {request.location}
- Use varied teaching methods (visual, auditory, kinesthetic)
- Include formative and summative assessment
- Provide differentiation strategies
- Real-world applications
- Interactive elements

Teaching Strategies:
- Direct instruction
- Guided practice
- Independent work
- Group activities
- Discussion and reflection

Additional requirements: {request.additional_requirements or 'None'}

Create an engaging, culturally relevant lesson that achieves clear learning outcomes."""


# Create a singleton instance
hyper_local_content_service = HyperLocalContentService()
