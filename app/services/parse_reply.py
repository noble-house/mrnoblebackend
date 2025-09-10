from dateutil import parser as dtp
from datetime import datetime, timedelta
import re
from typing import List, Dict, Optional
from ..services.logger import log_error, get_logger
from ..services.ai_service import ai_service

logger = get_logger("email_parser")

class EmailParser:
    """Enhanced email parsing service with AI and NLP capabilities."""
    
    def __init__(self):
        self.time_patterns = [
            r'\b\d{1,2}:\d{2}\s*(?:am|pm|AM|PM)\b',
            r'\b\d{1,2}:\d{2}\b',
            r'\b(?:morning|afternoon|evening|night)\b',
            r'\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
            r'\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b',
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b\d{4}-\d{2}-\d{2}\b'
        ]
    
    async def extract_slots_from_text(self, text: str) -> List[Dict[str, str]]:
        """Extract time slots from email text using AI and NLP."""
        try:
            if not text or len(text.strip()) < 10:
                return []
            
            # First try AI-powered extraction
            ai_slots = await self._extract_slots_with_ai(text)
            if ai_slots:
                return ai_slots[:3]
            
            # Fallback to rule-based extraction
            return self._extract_slots_with_rules(text)
            
        except Exception as e:
            log_error(e, context={"operation": "extract_slots_from_text", "text_length": len(text)})
            return []
    
    async def _extract_slots_with_ai(self, text: str) -> List[Dict[str, str]]:
        """Use AI to extract time slots from email text."""
        try:
            prompt = f"""
            Extract available time slots from this email text.
            Return a JSON array of objects with keys: start, end, description.
            Each slot should be a 1-hour duration.
            Use ISO format for dates (YYYY-MM-DDTHH:MM:SS).
            If no clear time slots are found, return an empty array.
            
            Email text:
            {text[:1500]}  # Limit to first 1500 chars
            """
            
            response = await ai_service.openai.ChatCompletion.acreate(
                model=ai_service.chat_model,
                messages=[
                    {"role": "system", "content": "You are a scheduling assistant extracting time slots from emails. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.1
            )
            
            slots_text = response.choices[0].message.content.strip()
            import json
            try:
                slots = json.loads(slots_text)
                if isinstance(slots, list):
                    # Validate and clean the slots
                    valid_slots = []
                    for slot in slots:
                        if isinstance(slot, dict) and 'start' in slot and 'end' in slot:
                            try:
                                # Validate datetime format
                                start_dt = datetime.fromisoformat(slot['start'].replace('Z', '+00:00'))
                                end_dt = datetime.fromisoformat(slot['end'].replace('Z', '+00:00'))
                                
                                # Ensure end is after start
                                if end_dt > start_dt:
                                    valid_slots.append({
                                        "start": slot['start'],
                                        "end": slot['end'],
                                        "description": slot.get('description', '')
                                    })
                            except ValueError:
                                continue
                    return valid_slots
            except json.JSONDecodeError:
                pass
            
            return []
            
        except Exception as e:
            log_error(e, context={"operation": "_extract_slots_with_ai", "text_length": len(text)})
            return []
    
    def _extract_slots_with_rules(self, text: str) -> List[Dict[str, str]]:
        """Fallback rule-based time slot extraction."""
        try:
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            slots = []
            
            for line in lines:
                # Skip lines that are too short or don't contain time indicators
                if len(line) < 5 or not any(re.search(pattern, line, re.IGNORECASE) for pattern in self.time_patterns):
                    continue
                
                try:
                    # Try to parse the line as a datetime
                    start = dtp.parse(line, fuzzy=True)
                    
                    # Skip if the date is too far in the past or future
                    now = datetime.now()
                    if start < now - timedelta(days=1) or start > now + timedelta(days=90):
                        continue
                    
                    # Create a 1-hour slot
                    end = start + timedelta(minutes=60)
                    
                    slots.append({
                        "start": start.isoformat(),
                        "end": end.isoformat(),
                        "description": line[:100]  # Truncate description
                    })
                    
                except Exception:
                    continue
            
            return slots[:3]
            
        except Exception as e:
            log_error(e, context={"operation": "_extract_slots_with_rules", "text_length": len(text)})
            return []
    
    def validate_slot_format(self, slot: Dict[str, str]) -> bool:
        """Validate that a time slot has the correct format."""
        try:
            if not isinstance(slot, dict) or 'start' not in slot or 'end' not in slot:
                return False
            
            start_dt = datetime.fromisoformat(slot['start'].replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(slot['end'].replace('Z', '+00:00'))
            
            # Check that end is after start and duration is reasonable (1-4 hours)
            duration = (end_dt - start_dt).total_seconds() / 3600
            return 0.5 <= duration <= 4.0
            
        except (ValueError, TypeError):
            return False
    
    def clean_and_normalize_text(self, text: str) -> str:
        """Clean and normalize email text for better parsing."""
        try:
            if not text:
                return ""
            
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', '', text)
            
            # Normalize whitespace
            text = re.sub(r'\s+', ' ', text)
            
            # Remove common email signatures and footers
            text = re.sub(r'(?i)(best regards|sincerely|thanks|thank you).*$', '', text, flags=re.MULTILINE)
            
            # Remove quoted text (replies)
            text = re.sub(r'^>.*$', '', text, flags=re.MULTILINE)
            
            return text.strip()
            
        except Exception as e:
            log_error(e, context={"operation": "clean_and_normalize_text"})
            return text

# Global instance
email_parser = EmailParser()

# Backward compatibility function
async def extract_slots_from_text(text: str) -> List[Dict[str, str]]:
    """Backward compatible function for extracting time slots."""
    return await email_parser.extract_slots_from_text(text)
