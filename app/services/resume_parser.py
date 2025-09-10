import re
import requests
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
from ..services.ai_service import ai_service
from ..services.logger import log_error, get_logger

logger = get_logger("resume_parser")

class ResumeParser:
    """Service for parsing resumes and extracting information."""
    
    def __init__(self):
        self.supported_extensions = {'.pdf', '.doc', '.docx', '.txt'}
    
    async def parse_resume_from_url(self, url: str) -> Dict[str, any]:
        """Parse resume from URL and extract information."""
        try:
            # Download the resume content
            content = await self._download_resume(url)
            if not content:
                return {"text": "", "skills": [], "experience": [], "education": []}
            
            # Extract text content
            text_content = await self._extract_text_from_content(content, url)
            
            # Extract structured information using AI
            skills = await ai_service.extract_skills_from_text(text_content)
            experience = await self._extract_experience(text_content)
            education = await self._extract_education(text_content)
            
            return {
                "text": text_content,
                "skills": skills,
                "experience": experience,
                "education": education,
                "url": url
            }
            
        except Exception as e:
            log_error(e, context={"operation": "parse_resume_from_url", "url": url})
            return {"text": "", "skills": [], "experience": [], "education": [], "error": str(e)}
    
    async def parse_resume_from_text(self, text: str) -> Dict[str, any]:
        """Parse resume from text content."""
        try:
            if not text or len(text.strip()) < 50:
                return {"text": text, "skills": [], "experience": [], "education": []}
            
            # Extract structured information using AI
            skills = await ai_service.extract_skills_from_text(text)
            experience = await self._extract_experience(text)
            education = await self._extract_education(text)
            
            return {
                "text": text,
                "skills": skills,
                "experience": experience,
                "education": education
            }
            
        except Exception as e:
            log_error(e, context={"operation": "parse_resume_from_text", "text_length": len(text)})
            return {"text": text, "skills": [], "experience": [], "education": [], "error": str(e)}
    
    async def _download_resume(self, url: str) -> Optional[bytes]:
        """Download resume content from URL."""
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError("Invalid URL")
            
            # Check file extension
            path = parsed_url.path.lower()
            if not any(path.endswith(ext) for ext in self.supported_extensions):
                logger.warning(f"Unsupported file extension in URL: {url}")
            
            # Download with timeout
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Check content size (limit to 10MB)
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > 10 * 1024 * 1024:
                raise ValueError("File too large (max 10MB)")
            
            return response.content
            
        except Exception as e:
            log_error(e, context={"operation": "_download_resume", "url": url})
            return None
    
    async def _extract_text_from_content(self, content: bytes, url: str) -> str:
        """Extract text from resume content based on file type."""
        try:
            path = urlparse(url).path.lower()
            
            if path.endswith('.txt'):
                return content.decode('utf-8', errors='ignore')
            elif path.endswith('.pdf'):
                return await self._extract_text_from_pdf(content)
            elif path.endswith(('.doc', '.docx')):
                return await self._extract_text_from_doc(content)
            else:
                # Try to decode as text
                return content.decode('utf-8', errors='ignore')
                
        except Exception as e:
            log_error(e, context={"operation": "_extract_text_from_content", "url": url})
            return ""
    
    async def _extract_text_from_pdf(self, content: bytes) -> str:
        """Extract text from PDF content."""
        try:
            # Try to import PyPDF2, fallback to basic extraction if not available
            try:
                import PyPDF2
                import io
                
                pdf_file = io.BytesIO(content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                text_content = ""
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text_content += page.extract_text() + "\n"
                
                return text_content.strip()
                
            except ImportError:
                # Fallback: try to extract text using basic string operations
                # This is a simplified approach for when PyPDF2 is not available
                try:
                    # Look for text patterns in the PDF binary content
                    content_str = content.decode('utf-8', errors='ignore')
                    # Extract readable text patterns
                    import re
                    text_patterns = re.findall(r'[A-Za-z0-9\s\.\,\;\:\!\?\-\(\)]{10,}', content_str)
                    return ' '.join(text_patterns[:50])  # Limit to first 50 patterns
                except:
                    return "PDF content extraction requires PyPDF2 library. Please install it for full functionality."
                    
        except Exception as e:
            log_error(e, context={"operation": "_extract_text_from_pdf"})
            return ""
    
    async def _extract_text_from_doc(self, content: bytes) -> str:
        """Extract text from DOC/DOCX content."""
        try:
            # Try to import python-docx for DOCX files
            try:
                from docx import Document
                import io
                
                doc_file = io.BytesIO(content)
                doc = Document(doc_file)
                
                text_content = ""
                for paragraph in doc.paragraphs:
                    text_content += paragraph.text + "\n"
                
                return text_content.strip()
                
            except ImportError:
                # Fallback for DOC files or when python-docx is not available
                try:
                    # Try to extract text using basic string operations
                    content_str = content.decode('utf-8', errors='ignore')
                    # Extract readable text patterns
                    import re
                    text_patterns = re.findall(r'[A-Za-z0-9\s\.\,\;\:\!\?\-\(\)]{10,}', content_str)
                    return ' '.join(text_patterns[:50])  # Limit to first 50 patterns
                except:
                    return "DOC/DOCX content extraction requires python-docx library. Please install it for full functionality."
                    
        except Exception as e:
            log_error(e, context={"operation": "_extract_text_from_doc"})
            return ""
    
    async def _extract_experience(self, text: str) -> List[Dict[str, str]]:
        """Extract work experience from resume text."""
        try:
            if not text or len(text.strip()) < 50:
                return []
            
            # Use AI to extract experience
            prompt = f"""
            Extract work experience from this resume text.
            Return a JSON array of objects with keys: company, position, duration, description.
            
            Resume text:
            {text[:2000]}  # Limit to first 2000 chars
            """
            
            response = await ai_service.openai.ChatCompletion.acreate(
                model=ai_service.chat_model,
                messages=[
                    {"role": "system", "content": "You are a recruiter extracting work experience from resumes. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.1
            )
            
            experience_text = response.choices[0].message.content.strip()
            import json
            try:
                experience = json.loads(experience_text)
                if isinstance(experience, list):
                    return experience
            except json.JSONDecodeError:
                pass
            
            return []
            
        except Exception as e:
            log_error(e, context={"operation": "_extract_experience", "text_length": len(text)})
            return []
    
    async def _extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education from resume text."""
        try:
            if not text or len(text.strip()) < 50:
                return []
            
            # Use AI to extract education
            prompt = f"""
            Extract education information from this resume text.
            Return a JSON array of objects with keys: institution, degree, field, year.
            
            Resume text:
            {text[:2000]}  # Limit to first 2000 chars
            """
            
            response = await ai_service.openai.ChatCompletion.acreate(
                model=ai_service.chat_model,
                messages=[
                    {"role": "system", "content": "You are a recruiter extracting education from resumes. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.1
            )
            
            education_text = response.choices[0].message.content.strip()
            import json
            try:
                education = json.loads(education_text)
                if isinstance(education, list):
                    return education
            except json.JSONDecodeError:
                pass
            
            return []
            
        except Exception as e:
            log_error(e, context={"operation": "_extract_education", "text_length": len(text)})
            return []

# Global instance
resume_parser = ResumeParser()
