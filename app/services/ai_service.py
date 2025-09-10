import openai
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple, Optional
import hashlib
from ..config import settings
from ..services.logger import log_error, get_logger
from ..services.cache import cache_service, CacheKeys

logger = get_logger("ai_service")

# Initialize OpenAI client
openai.api_key = settings.OPENAI_API_KEY
openai.api_base = settings.OPENAI_BASE_URL

class AIService:
    """Service for AI-powered matching and analysis."""
    
    def __init__(self):
        self.embedding_model = "text-embedding-ada-002"
        self.chat_model = "gpt-3.5-turbo"
    
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding for a text using OpenAI with caching."""
        try:
            if not text or not text.strip():
                return None
            
            # Create cache key from text hash
            text_hash = hashlib.md5(text.strip().encode()).hexdigest()
            cache_key = CacheKeys.ai_embedding(text_hash)
            
            # Try to get from cache first
            cached_embedding = cache_service.get(cache_key)
            if cached_embedding is not None:
                logger.info("Embedding retrieved from cache", text_hash=text_hash)
                return cached_embedding
                
            # Get from OpenAI
            response = await openai.Embedding.acreate(
                model=self.embedding_model,
                input=text.strip()
            )
            embedding = response['data'][0]['embedding']
            
            # Cache the result (24 hour TTL for embeddings)
            cache_service.set(cache_key, embedding, ttl=86400)
            logger.info("Embedding cached", text_hash=text_hash)
            
            return embedding
        except Exception as e:
            log_error(e, context={"operation": "get_embedding", "text_length": len(text)})
            return None
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Get embeddings for multiple texts."""
        try:
            # Filter out empty texts
            valid_texts = [text.strip() for text in texts if text and text.strip()]
            if not valid_texts:
                return [None] * len(texts)
            
            response = await openai.Embedding.acreate(
                model=self.embedding_model,
                input=valid_texts
            )
            
            embeddings = response['data']
            result = []
            valid_idx = 0
            
            for text in texts:
                if text and text.strip():
                    result.append(embeddings[valid_idx]['embedding'])
                    valid_idx += 1
                else:
                    result.append(None)
            
            return result
        except Exception as e:
            log_error(e, context={"operation": "get_embeddings_batch", "text_count": len(texts)})
            return [None] * len(texts)
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        try:
            if not embedding1 or not embedding2:
                return 0.0
            
            # Convert to numpy arrays and reshape for cosine_similarity
            vec1 = np.array(embedding1).reshape(1, -1)
            vec2 = np.array(embedding2).reshape(1, -1)
            
            similarity = cosine_similarity(vec1, vec2)[0][0]
            return float(similarity)
        except Exception as e:
            log_error(e, context={"operation": "calculate_similarity"})
            return 0.0
    
    async def extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skills from resume text using AI with caching."""
        try:
            if not text or len(text.strip()) < 50:
                return []
            
            # Create cache key from text hash
            text_hash = hashlib.md5(text.strip().encode()).hexdigest()
            cache_key = CacheKeys.ai_skills(text_hash)
            
            # Try to get from cache first
            cached_skills = cache_service.get(cache_key)
            if cached_skills is not None:
                logger.info("Skills retrieved from cache", text_hash=text_hash)
                return cached_skills
            
            prompt = f"""
            Extract technical skills and technologies from the following resume text.
            Return only a JSON array of skill names, no explanations.
            Focus on programming languages, frameworks, tools, and technologies.
            
            Resume text:
            {text[:2000]}  # Limit to first 2000 chars
            """
            
            response = await openai.ChatCompletion.acreate(
                model=self.chat_model,
                messages=[
                    {"role": "system", "content": "You are a technical recruiter extracting skills from resumes. Return only a JSON array of skill names."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            skills_text = response.choices[0].message.content.strip()
            # Try to parse as JSON array
            import json
            try:
                skills = json.loads(skills_text)
                if isinstance(skills, list):
                    result = [skill.strip() for skill in skills if isinstance(skill, str) and skill.strip()]
                else:
                    result = []
            except json.JSONDecodeError:
                # Fallback: split by common delimiters
                skills = [skill.strip() for skill in skills_text.replace('[', '').replace(']', '').split(',')]
                result = [skill.strip('"\'') for skill in skills if skill.strip()]
            
            # Cache the result (12 hour TTL for skills)
            cache_service.set(cache_key, result, ttl=43200)
            logger.info("Skills cached", text_hash=text_hash, skills_count=len(result))
            
            return result
        except Exception as e:
            log_error(e, context={"operation": "extract_skills_from_text", "text_length": len(text)})
            return []
    
    async def analyze_job_requirements(self, job_description: str) -> Dict[str, any]:
        """Analyze job description to extract requirements and preferences."""
        try:
            if not job_description or len(job_description.strip()) < 50:
                return {"must_have": [], "nice_to_have": [], "experience_level": "unknown"}
            
            prompt = f"""
            Analyze this job description and extract:
            1. Must-have technical skills (required)
            2. Nice-to-have skills (preferred)
            3. Experience level (junior/mid/senior)
            
            Return a JSON object with keys: must_have, nice_to_have, experience_level
            
            Job description:
            {job_description[:2000]}  # Limit to first 2000 chars
            """
            
            response = await openai.ChatCompletion.acreate(
                model=self.chat_model,
                messages=[
                    {"role": "system", "content": "You are a technical recruiter analyzing job descriptions. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.1
            )
            
            analysis_text = response.choices[0].message.content.strip()
            import json
            try:
                analysis = json.loads(analysis_text)
                return {
                    "must_have": analysis.get("must_have", []),
                    "nice_to_have": analysis.get("nice_to_have", []),
                    "experience_level": analysis.get("experience_level", "unknown")
                }
            except json.JSONDecodeError:
                return {"must_have": [], "nice_to_have": [], "experience_level": "unknown"}
                
        except Exception as e:
            log_error(e, context={"operation": "analyze_job_requirements", "text_length": len(job_description)})
            return {"must_have": [], "nice_to_have": [], "experience_level": "unknown"}
    
    async def compute_match_score(
        self, 
        job_description: str, 
        job_requirements: Dict[str, List[str]], 
        resume_text: str, 
        resume_skills: List[str]
    ) -> Tuple[float, str, List[str]]:
        """Compute comprehensive match score between job and candidate."""
        try:
            # Get embeddings for job description and resume
            job_embedding = await self.get_embedding(job_description)
            resume_embedding = await self.get_embedding(resume_text)
            
            # Calculate semantic similarity
            semantic_score = 0.0
            if job_embedding and resume_embedding:
                semantic_score = self.calculate_similarity(job_embedding, resume_embedding)
            
            # Calculate skill-based matching
            must_have_skills = set(job_requirements.get("must_have", []))
            nice_to_have_skills = set(job_requirements.get("nice_to_have", []))
            candidate_skills = set(resume_skills)
            
            # Must-have skills matching (critical)
            must_have_matches = must_have_skills.intersection(candidate_skills)
            must_have_missing = must_have_skills - candidate_skills
            
            # Nice-to-have skills matching (bonus)
            nice_to_have_matches = nice_to_have_skills.intersection(candidate_skills)
            
            # Calculate scores
            must_have_score = len(must_have_matches) / max(len(must_have_skills), 1)
            nice_to_have_score = len(nice_to_have_matches) / max(len(nice_to_have_skills), 1) * 0.3
            
            # Combine scores (semantic similarity + skill matching)
            skill_score = must_have_score + nice_to_have_score
            final_score = (semantic_score * 0.4) + (skill_score * 0.6)
            
            # Determine status
            if must_have_missing:
                status = "NOT_FIT"
            elif final_score >= 0.75:
                status = "FIT"
            elif final_score >= 0.5:
                status = "BORDERLINE"
            else:
                status = "NOT_FIT"
            
            # Generate reasons
            reasons = []
            if must_have_matches:
                reasons.append(f"Matched must-have skills: {', '.join(must_have_matches)}")
            if must_have_missing:
                reasons.append(f"Missing must-have skills: {', '.join(must_have_missing)}")
            if nice_to_have_matches:
                reasons.append(f"Bonus skills: {', '.join(nice_to_have_matches)}")
            if semantic_score > 0.7:
                reasons.append("High semantic similarity to job description")
            
            return final_score, status, reasons
            
        except Exception as e:
            log_error(e, context={"operation": "compute_match_score"})
            return 0.0, "NOT_FIT", ["Error in matching process"]

# Global instance
ai_service = AIService()
