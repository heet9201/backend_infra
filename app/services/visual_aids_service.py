from app.models.agent_model import (
    VisualAidRequest, VisualAidResponse, AgentType, Language, VisualAidType, 
    VisualAid, Subject, SessionInfo
)
from app.core.vertex_ai import generate_educational_content, generate_image
from app.utils.logger import logger
from app.services.session_service import session_service
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import re
import random

class VisualAidsService:
    """Service for generating blackboard-friendly visual aids for educational use"""
    
    def __init__(self):
        self.subject_templates = {
            Subject.SCIENCE: {
                "water_cycle": "A circular diagram showing evaporation from bodies of water, condensation in clouds, precipitation as rain/snow, and collection in water bodies",
                "solar_system": "Concentric circles showing planets around the sun with relative distances and sizes",
                "plant_cell": "Oval shape with labeled organelles including nucleus, cell wall, chloroplasts, and vacuole",
                "food_chain": "Linear diagram showing energy flow from producers to consumers to decomposers",
            },
            Subject.MATHEMATICS: {
                "coordinate_plane": "A grid with x and y axes, showing quadrants and sample points",
                "geometric_shapes": "Various 2D shapes (triangle, square, circle) with labeled properties",
                "fraction_model": "Circular or rectangular shapes divided into equal parts with some portions shaded",
                "number_line": "Horizontal line with evenly spaced tick marks and labeled integers",
            },
            Subject.SOCIAL_STUDIES: {
                "map_elements": "Simple outline map with labeled features like mountains, rivers, and cities",
                "timeline": "Horizontal line with significant events marked chronologically",
                "community_helpers": "Simple figures representing different community roles with their tools",
                "government_structure": "Hierarchical diagram showing levels of government and their relationships",
            },
            Subject.ENVIRONMENTAL_SCIENCE: {
                "ecosystem": "Landscape showing interconnected habitats with plants and animals",
                "pollution_sources": "Diagram showing various pollution sources and their effects",
                "renewable_energy": "Illustrations of solar panels, wind turbines, and hydroelectric dams",
                "waste_management": "Flow chart showing waste reduction, reuse, recycling, and disposal",
            }
        }
        
        # Base elements for simple drawings
        self.drawing_elements = {
            "basic_shapes": ["circle", "square", "triangle", "rectangle", "oval", "arrow"],
            "lines": ["straight", "curved", "dashed", "dotted", "wavy"],
            "text_elements": ["labels", "captions", "titles", "legends"],
            "connectors": ["arrows", "lines", "brackets", "dotted connectors"]
        }
    
    def generate_visual_aid(self, request: VisualAidRequest, user_id: Optional[str] = None) -> VisualAidResponse:
        """Generate blackboard-friendly visual aid based on the request"""
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
                    content=f"Generate {request.visual_type.value} about {request.topic} for grade {request.grade_levels}",
                    agent_type="user",
                    metadata={
                        "language": request.language.value,
                        "topic": request.topic,
                        "visual_type": request.visual_type.value,
                        "subject": request.subject.value
                    }
                )
            
            # Generate visual aid
            prompt = self._generate_visual_aid_prompt(request)
            response_text = generate_educational_content(prompt, request.language.value)
            
            # Extract drawing instructions and teaching tips
            drawing_instructions = self._extract_drawing_instructions(response_text)
            teaching_tips = self._extract_teaching_tips(response_text)
            
            # Generate image and get local file path
            image_file_path = self._generate_image_url(request)
            
            # Convert to URL for client access
            image_url = self._file_path_to_url(image_file_path)
            
            # Create visual aid object
            topic = request.topic if request.topic else self._extract_topic_from_description(request.description)
            visual_aid = VisualAid(
                title=f"{topic} - {request.visual_type.value}",
                description=request.description,
                image_url=image_url,
                image_path=image_file_path,
                drawing_instructions=drawing_instructions,
                visual_type=request.visual_type,
                complexity=request.complexity,
                estimated_drawing_time=self._estimate_drawing_time(request),
                labels=self._extract_labels(response_text),
                teaching_tips=teaching_tips
            )
            
            # Calculate generation time
            generation_time = str(datetime.now() - start_time)
            
            # Create response object
            response = VisualAidResponse(
                status="success",
                agent_type=AgentType.VISUAL_AIDS,
                language=request.language,
                subject=request.subject.value,
                grade_levels=request.grade_levels,
                visual_aids=[visual_aid],
                generation_time=generation_time,
                metadata={
                    "topic": request.topic,
                    "visual_type": request.visual_type.value,
                    "complexity": request.complexity,
                    "blackboard_friendly": request.blackboard_friendly
                }
            )
            
            # Add agent response to session if user_id is provided
            if user_id:
                user_session = session_service.get_session(user_id)
                session_service.add_message(
                    user_id=user_id,
                    content=f"Generated visual aid for {request.topic}",
                    agent_type=AgentType.VISUAL_AIDS.value,
                    metadata={
                        "language": request.language.value,
                        "topic": request.topic,
                        "visual_type": request.visual_type.value,
                        "status": "success"
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
            logger.error(f"Error generating visual aid: {e}")
            error_response = VisualAidResponse(
                status="error",
                agent_type=AgentType.VISUAL_AIDS,
                language=request.language,
                subject=request.subject.value,
                grade_levels=request.grade_levels,
                visual_aids=[],
                error_message=str(e),
                generation_time=str(datetime.now() - start_time)
            )
            
            # Add error response to session if user_id is provided
            if user_id:
                try:
                    user_session = session_service.get_session(user_id)
                    session_service.add_message(
                        user_id=user_id,
                        content=f"Error generating visual aid for {request.topic}: {str(e)}",
                        agent_type=AgentType.VISUAL_AIDS.value,
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
    
    def _generate_visual_aid_prompt(self, request: VisualAidRequest) -> str:
        """Generate prompt for creating a visual aid based primarily on the description"""
        complexity_guide = {
            "simple": "Use minimal elements, focus on core concepts only, 3-5 components max",
            "medium": "Include main concepts with some supporting details, 5-8 components",
            "detailed": "Include comprehensive details while keeping it drawable, 8-12 components max"
        }
        
        complexity_level = complexity_guide.get(request.complexity.lower(), complexity_guide["medium"])
        
        # Extract topic from description if not provided
        topic = request.topic if request.topic else self._extract_topic_from_description(request.description)
        
        # Get subject-specific template if available
        subject_templates = self.subject_templates.get(request.subject, {})
        template_suggestion = ""
        
        for key, template in subject_templates.items():
            if topic and (key.lower() in topic.lower() or topic.lower() in key.lower()):
                template_suggestion = f"\nReference template: {template}"
                break
        
        # Determine the appropriate visual type based on description if not specified
        visual_type = request.visual_type.value
        grade_level_text = ', '.join(map(str, request.grade_levels)) if request.grade_levels else "middle school"
        
        return f"""Create step-by-step instructions for drawing a simple visual based on this description: 
"{request.description}"

Subject: {request.subject.value}
Topic: {topic}
Visual type: {visual_type}
Grade level: {grade_level_text}
Complexity: {request.complexity} - {complexity_level}
Intended for: Drawing on a {request.color_scheme} in a classroom setting
Include labels: {"Yes" if request.include_labels else "No"}
Include teaching instructions: {"Yes" if request.include_instructions else "No"}{template_suggestion}

Format your response in these sections:
1. DRAWING TITLE: Short, descriptive title
2. MATERIALS NEEDED: Basic chalk/markers and any other materials
3. STEP-BY-STEP DRAWING INSTRUCTIONS: Numbered steps (6-10 steps), each simple enough for a teacher to follow
4. KEY LABELS: 3-8 important elements to label in the drawing
5. TEACHING TIPS: 2-4 suggestions for using this visual effectively in teaching

Important Guidelines:
- Focus on creating a visual aid that DIRECTLY represents the user's description
- Create instructions for a SIMPLE, CLEAR drawing that can be quickly reproduced on a blackboard
- Focus on clarity over detail - use basic shapes and lines
- Ensure the final drawing will fit on a standard blackboard
- Use only features that can be created with chalk/basic markers
- Avoid complex shading or tiny details
- Ensure the visual aid effectively communicates the key concept

Example elements to include: {", ".join(random.sample(self.drawing_elements["basic_shapes"], 2) + random.sample(self.drawing_elements["lines"], 1) + random.sample(self.drawing_elements["text_elements"], 1))}

Additional requirements: {request.additional_requirements or "Keep it simple and clear"}"""
    
    def _extract_drawing_instructions(self, response_text: str) -> str:
        """Extract step-by-step drawing instructions from response text"""
        instructions_pattern = r"STEP-BY-STEP DRAWING INSTRUCTIONS:(.*?)(?:KEY LABELS:|TEACHING TIPS:|$)"
        instructions_match = re.search(instructions_pattern, response_text, re.DOTALL | re.IGNORECASE)
        
        if instructions_match:
            return instructions_match.group(1).strip()
        
        # If specific section isn't found, return the whole text
        return response_text
    
    def _extract_teaching_tips(self, response_text: str) -> List[str]:
        """Extract teaching tips from response text"""
        tips_pattern = r"TEACHING TIPS:(.*?)(?:$)"
        tips_match = re.search(tips_pattern, response_text, re.DOTALL | re.IGNORECASE)
        
        if tips_match:
            tips_text = tips_match.group(1).strip()
            # Split by numbered items or bullet points
            tips = re.split(r'\d+\.|\-', tips_text)
            return [tip.strip() for tip in tips if tip.strip()]
        
        return []
    
    def _extract_labels(self, response_text: str) -> List[str]:
        """Extract key labels from response text"""
        labels_pattern = r"KEY LABELS:(.*?)(?:TEACHING TIPS:|$)"
        labels_match = re.search(labels_pattern, response_text, re.DOTALL | re.IGNORECASE)
        
        if labels_match:
            labels_text = labels_match.group(1).strip()
            # Split by numbered items or bullet points
            labels = re.split(r'\d+\.|\-', labels_text)
            return [label.strip() for label in labels if label.strip()]
        
        return []
    
    def _estimate_drawing_time(self, request: VisualAidRequest) -> str:
        """Estimate time to complete the drawing"""
        complexity_times = {
            "simple": "2-3",
            "medium": "4-6",
            "detailed": "7-10"
        }
        
        return f"{complexity_times.get(request.complexity.lower(), '5')} minutes"
    
    def _extract_topic_from_description(self, description: str) -> str:
        """Extract a topic from the description using intelligent parsing"""
        # Return a default if no description
        if not description:
            return "educational visual aid"
            
        # Try to extract a reasonable topic from the first sentence
        first_sentence = description.split('.')[0]
        # If first sentence is too long, take first 5-10 words
        words = first_sentence.split()
        
        if len(words) <= 5:
            return first_sentence
        else:
            # Look for common topic patterns like "about", "on", "for", "of", etc.
            for idx, word in enumerate(words[:10]):
                if word.lower() in ["about", "on", "for", "of", "regarding"] and idx < len(words) - 1:
                    return " ".join(words[idx+1:min(idx+6, len(words))])
            
            # If no pattern found, take first 5 words
            return " ".join(words[:5])
            
    def _analyze_visual_context(self, request: VisualAidRequest, topic: str) -> str:
        """Analyze the context of the visual aid to generate a deeper understanding"""
        import random
        
        # Define contextual frameworks based on subject areas
        science_contexts = [
            f"a conceptual model showing the key processes involved in {topic}",
            f"a visual representation of the structure and components of {topic}",
            f"an illustrated explanation of how {topic} works and its significance",
            f"a comparative visualization showing different aspects of {topic}"
        ]
        
        math_contexts = [
            f"a visual representation of {topic} showing mathematical relationships",
            f"an illustrated explanation of the {topic} concept with examples",
            f"a step-by-step visual guide to understanding {topic}",
            f"a conceptual model demonstrating how {topic} applies in different situations"
        ]
        
        social_contexts = [
            f"a visual overview of key concepts in {topic}",
            f"an illustrated timeline or process diagram explaining {topic}",
            f"a conceptual map showing relationships between aspects of {topic}",
            f"a visual representation comparing different perspectives on {topic}"
        ]
        
        # Select context framework based on subject
        if request.subject.value.lower() in ["science", "biology", "chemistry", "physics"]:
            contexts = science_contexts
        elif request.subject.value.lower() in ["mathematics", "math", "algebra", "geometry"]:
            contexts = math_contexts
        else:
            contexts = social_contexts
            
        # Select a random context appropriate for the subject area
        # This ensures variety in the generated images
        selected_context = random.choice(contexts)
        
        # Enhance with visual type specific details
        if request.visual_type.value == "flowchart":
            selected_context += " with a clear process flow and directional indicators"
        elif request.visual_type.value == "chart":
            selected_context += " with organized data visualization elements"
        elif request.visual_type.value == "concept_map":
            selected_context += " highlighting connections between ideas"
            
        return selected_context
        
    def _determine_pedagogical_approach(self, subject, grade_range: str) -> str:
        """Determine appropriate pedagogical approach based on subject and grade level"""
        import random
        
        # Extract approximate age/grade level
        is_elementary = any(str(i) in grade_range for i in range(1, 6))
        is_middle = any(str(i) in grade_range for i in range(6, 9)) or "middle" in grade_range.lower()
        is_high = any(str(i) in grade_range for i in range(9, 13)) or "high" in grade_range.lower()
        
        # Define pedagogical approaches by level and subject
        approaches = []
        
        if is_elementary:
            approaches.extend([
                "Concrete visual representations with simple, clear labels",
                "Engaging, colorful illustrations that capture attention and interest",
                "Simple visual storytelling to make concepts accessible",
                "Direct visual representation of concrete concepts"
            ])
        elif is_middle:
            approaches.extend([
                "Balanced concrete and abstract representations",
                "Visual analogies connecting new concepts to familiar ideas",
                "Clear organizational structures showing relationships between concepts",
                "Scaffolded visual explanations building conceptual understanding"
            ])
        elif is_high:
            approaches.extend([
                "Abstract representations emphasizing conceptual relationships",
                "Sophisticated visual models showing multiple layers of understanding",
                "Visual synthesis of complex ideas and their applications",
                "Critical analysis frameworks presented visually"
            ])
        else:
            # Default to a general approach
            approaches.extend([
                "Clear visual representation appropriate for diverse learners",
                "Balanced concrete and abstract visual elements",
                "Structured visual framework highlighting key concepts"
            ])
        
        # Select a random approach from appropriate options
        # This ensures variety in the educational approach
        return random.choice(approaches)
        
    def _create_dynamic_style_guide(self, visual_type, subject) -> str:
        """Create a dynamic style guide based on visual type and subject"""
        import random
        
        # Base style elements that apply to all educational visuals
        base_style = [
            "Clean, professional educational design with clear purpose",
            "Thoughtful layout with proper spacing and visual hierarchy",
            "Appropriate use of color to highlight important concepts",
            "Clear labels integrated with visual elements",
            "White background for maximum clarity and focus"
        ]
        
        # Add style elements specific to the visual type
        type_specific = []
        
        if visual_type.value == "line_drawing":
            type_specific.extend([
                "Precise, confident line work with varying line weights",
                "Minimal shading only where necessary for clarity",
                "Clean contours defining all important elements"
            ])
        elif visual_type.value == "chart":
            type_specific.extend([
                "Clear axes with appropriate scales and labels",
                "Distinct data representations with strong visual contrast",
                "Legend explaining all visual elements used"
            ])
        elif visual_type.value == "diagram":
            type_specific.extend([
                "Precise illustration of components with clear boundaries",
                "Strategic use of cutaways or cross-sections where helpful",
                "Visual emphasis on key structural relationships"
            ])
        elif visual_type.value == "flowchart":
            type_specific.extend([
                "Clear directional indicators showing process flow",
                "Distinct shapes for different types of steps or decisions",
                "Logical layout that guides the eye through the process"
            ])
        elif visual_type.value == "concept_map":
            type_specific.extend([
                "Visually distinct nodes representing key concepts",
                "Clear connectors showing relationships between concepts",
                "Spatial organization that reflects conceptual relationships"
            ])
        
        # Combine base style with type-specific elements
        # Randomly select a subset to create variation
        combined_elements = base_style + random.sample(type_specific, min(2, len(type_specific)))
        
        # Format as bullet points
        return "\n".join(f"- {element}" for element in combined_elements)
        
    def _generate_creative_direction(self, request: VisualAidRequest, topic: str) -> str:
        """Generate a unique creative direction for this specific visual aid"""
        import random
        
        # Create a unique creative approach each time
        creative_approaches = [
            f"Create a {request.visual_type.value} that emphasizes the key relationships in {topic} through thoughtful visual hierarchy and organization.",
            f"Design a visually engaging {request.visual_type.value} that makes {topic} immediately understandable through clear visual storytelling.",
            f"Develop a {request.visual_type.value} that breaks down {topic} into clear, digestible components that build understanding step by step.",
            f"Create an elegant, minimalist {request.visual_type.value} that distills {topic} to its essential elements while maintaining clarity.",
            f"Design a visually rich {request.visual_type.value} that shows the interconnections within {topic} through thoughtful visual mapping."
        ]
        
        # Select a random creative approach
        main_direction = random.choice(creative_approaches)
        
        # Add specific guidance based on complexity
        if request.complexity.lower() == "simple":
            main_direction += "\n- Focus on the 3-5 most essential elements only"
            main_direction += "\n- Keep visual language straightforward and direct"
        elif request.complexity.lower() == "detailed":
            main_direction += "\n- Include important supporting details and nuances"
            main_direction += "\n- Create multiple layers of information while maintaining clarity"
        
        return main_direction
            
    def _file_path_to_url(self, file_path: str) -> str:
        """Convert a file path to a URL that can be accessed by clients"""
        import os
        
        if not file_path:
            return "/static/images/placeholder.png"
            
        # Handle different types of paths
        if file_path.startswith("http://") or file_path.startswith("https://"):
            # Already a web URL
            return file_path
        
        # Get current working directory - the project root
        base_dir = os.getcwd()
        
        # Handle generated_images directory
        if "generated_images" in file_path:
            # Extract the part after "generated_images"
            if "/generated_images/" in file_path:
                # Extract the filename
                filename = os.path.basename(file_path)
                return f"/generated_images/{filename}"
            elif file_path.endswith(".png") or file_path.endswith(".jpg"):
                # Just the filename
                filename = os.path.basename(file_path)
                return f"/generated_images/{filename}"
        
        # Handle static directory
        if "/static/" in file_path:
            parts = file_path.split("/static/")
            if len(parts) > 1:
                return f"/static/{parts[1]}"
        
        # If it's an absolute path in the project directory
        if file_path.startswith(base_dir):
            rel_path = os.path.relpath(file_path, base_dir)
            # Format according to the directory structure
            if rel_path.startswith("generated_images/"):
                return f"/{rel_path}"
            elif rel_path.startswith("static/"):
                return f"/{rel_path}"
            else:
                # If it's in some other directory, put it under generated_images URL path
                filename = os.path.basename(file_path)
                return f"/generated_images/{filename}"
                
        # If it's a file:// URL or other absolute path outside project
        if file_path.startswith("file://") or os.path.isabs(file_path):
            filename = os.path.basename(file_path)
            # We'll need to copy this file to our generated_images directory
            try:
                import shutil
                target_path = os.path.join(base_dir, "generated_images", filename)
                # Only copy if source exists and isn't the same as target
                if os.path.exists(file_path.replace("file://", "")) and file_path.replace("file://", "") != target_path:
                    shutil.copy2(file_path.replace("file://", ""), target_path)
                return f"/generated_images/{filename}"
            except Exception as e:
                logger.error(f"Error copying file to generated_images: {e}")
                return "/static/images/placeholder.png"
        
        # Default - if we can't determine the URL path
        return "/static/images/placeholder.png"
    
    def _generate_image_url(self, request: VisualAidRequest) -> str:
        """
        Generate a unique, context-aware image for the visual aid using AI generation
        and return local file path. Each generation creates a custom image based on
        the specific request parameters.
        
        This implementation:
        1. Creates a dynamic, customized prompt based on the educational context
        2. Generates a unique image using Vertex AI advanced models
        3. Returns a local file path to the freshly generated image
        """
        from app.core.vertex_ai import generate_image
        import os
        import random
        
        # Extract core concepts from the request
        topic = request.topic if request.topic else self._extract_topic_from_description(request.description)
        visual_type = request.visual_type.value if request.visual_type else "diagram"
        
        # Create a contextual understanding of what kind of visual this is
        contextual_understanding = self._analyze_visual_context(request, topic)
        
        # Define pedagogical goals based on grade level and subject
        grade_range = ', '.join(map(str, request.grade_levels)) if request.grade_levels else 'middle school'
        pedagogical_approach = self._determine_pedagogical_approach(request.subject, grade_range)
        
        # Create a dynamic style guide based on the visual type and subject
        style_attributes = self._create_dynamic_style_guide(request.visual_type, request.subject)
        
        # Generate a unique creative direction for this specific visual
        creative_direction = self._generate_creative_direction(request, topic)
        
        # Craft a detailed AI-optimized prompt for image generation
        image_prompt = f"""Create a unique, educational {visual_type} about "{topic}" for {request.subject.value} teaching.

SPECIFIC REQUEST: {request.description}

EDUCATIONAL CONCEPT: {contextual_understanding}

PEDAGOGICAL CONTEXT:
- Subject area: {request.subject.value}
- Student age group: {grade_range}
- Teaching approach: {pedagogical_approach}
- Learning objectives: To help students visualize and understand {topic} through clear visual representation

VISUAL SPECIFICATIONS:
{style_attributes}

CREATIVE DIRECTION:
{creative_direction}

IMPORTANT: Create a unique, custom visual that effectively communicates this specific educational concept.
"""
        
        # Generate the image and get local file path
        local_file_path = generate_image(image_prompt)
        
        if not local_file_path:
            logger.error("Image generation failed completely")
            # If all generation methods failed, return a fallback URL
            placeholder_path = os.path.join(os.getcwd(), "static", "images", "placeholder.png")
            return placeholder_path
            
        logger.info(f"Generated image saved at: {local_file_path}")
        
        # Return the actual file path - we'll convert to URL separately
        return local_file_path

# Create a singleton instance
visual_aids_service = VisualAidsService()
