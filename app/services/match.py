import asyncio
from typing import Dict, List, Tuple
from .ai_service import ai_service
from .logger import log_error, get_logger

logger = get_logger("match_service")

async def compute_fit_score_async(
    job_description: str,
    job_requirements: Dict[str, List[str]], 
    resume_text: str, 
    resume_skills: List[str]
) -> Tuple[float, str, List[str]]:
    """Compute fit score using AI-powered matching."""
    try:
        return await ai_service.compute_match_score(
            job_description, job_requirements, resume_text, resume_skills
        )
    except Exception as e:
        log_error(e, context={"operation": "compute_fit_score_async"})
        # Fallback to simple matching
        return compute_fit_score_fallback(job_requirements, resume_skills)

def compute_fit_score_fallback(jd_json: Dict, resume_json: Dict) -> Tuple[float, str, List[str]]:
    """Fallback simple matching when AI service is unavailable."""
    jd_must = set(jd_json.get("must_have", []))
    res_skills = set(resume_json.get("skills", []))
    skills_overlap = len(jd_must & res_skills)
    must_miss = list(jd_must - res_skills)
    base = 0.5 + (0.1 * skills_overlap) - (0.05 * len(must_miss))
    score = max(0.0, min(1.0, base))
    status = "FIT" if score >= 0.70 else ("BORDERLINE" if score >= 0.55 else "NOT_FIT")
    reasons = ["Matched skills: " + ", ".join(jd_must & res_skills) if jd_must & res_skills else "No overlaps",
               "Missing must-haves: " + ", ".join(must_miss) if must_miss else "All must-haves present"]
    return score, status, reasons

def compute_fit_score(jd_json: Dict, resume_json: Dict) -> Tuple[float, str, List[str]]:
    """Synchronous wrapper for the async matching function."""
    try:
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an async context, we need to use a different approach
            # For now, fall back to simple matching
            logger.warning("Running in async context, using fallback matching")
            return compute_fit_score_fallback(jd_json, resume_json)
        else:
            # We can run the async function
            return loop.run_until_complete(
                compute_fit_score_async(
                    "",  # job_description - would need to be passed from the model
                    jd_json,
                    "",  # resume_text - would need to be passed from the model
                    resume_json.get("skills", [])
                )
            )
    except Exception as e:
        log_error(e, context={"operation": "compute_fit_score"})
        return compute_fit_score_fallback(jd_json, resume_json)
