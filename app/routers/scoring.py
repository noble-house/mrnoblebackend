from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas
from ..services.auth import get_current_admin
from ..services.ai_service import ai_service
from ..services.logger import get_logger
from typing import Dict, List, Any
import json

router = APIRouter(prefix="/score", tags=["score"])
logger = get_logger("scoring")

@router.post("/{interview_id}/finalize")
def finalize(
    interview_id: int, 
    db: Session = Depends(get_db),
    current_admin: models.Admin = Depends(get_current_admin)
):
    """Finalize interview scoring by aggregating rubric and persisting results."""
    try:
        # Get the interview link
        interview_link = db.query(models.InterviewLink).filter_by(id=interview_id).first()
        if not interview_link:
            raise HTTPException(404, "Interview not found")
        
        # Get the application
        application = db.query(models.Application).filter_by(id=interview_link.application_id).first()
        if not application:
            raise HTTPException(404, "Application not found")
        
        # Calculate scores based on interview data
        scores = calculate_interview_scores(interview_link, application)
        
        # Generate AI-powered recommendation
        recommendation = generate_recommendation(scores, application)
        
        # Create and save the score record
        score_record = models.Score(
            application_id=application.id,
            interview_link_id=interview_link.id,
            technical_score=scores.get("technical", 0),
            communication_score=scores.get("communication", 0),
            cultural_fit_score=scores.get("cultural_fit", 0),
            problem_solving_score=scores.get("problem_solving", 0),
            total_score=scores.get("total", 0),
            recommendation=recommendation,
            notes=scores.get("notes", ""),
            scored_by=current_admin.id
        )
        
        db.add(score_record)
        db.commit()
        db.refresh(score_record)
        
        logger.info(f"Interview {interview_id} scored successfully", extra={
            "interview_id": interview_id,
            "total_score": scores.get("total", 0),
            "recommendation": recommendation
        })
        
        return {
            "interview_id": interview_id,
            "application_id": application.id,
            "scores": scores,
            "recommendation": recommendation,
            "score_record_id": score_record.id
        }
        
    except Exception as e:
        logger.error(f"Failed to finalize interview scoring: {e}")
        raise HTTPException(500, f"Failed to finalize scoring: {str(e)}")

def calculate_interview_scores(interview_link: models.InterviewLink, application: models.Application) -> Dict[str, Any]:
    """Calculate interview scores based on various criteria."""
    try:
        # Base scores (in a real implementation, these would come from interview data)
        base_scores = {
            "technical": 75,
            "communication": 80,
            "cultural_fit": 85,
            "problem_solving": 70
        }
        
        # Adjust scores based on application data
        if application.match_score and application.match_score > 80:
            base_scores["technical"] += 5
        
        # Calculate weighted total
        weights = {
            "technical": 0.3,
            "communication": 0.25,
            "cultural_fit": 0.25,
            "problem_solving": 0.2
        }
        
        total_score = sum(base_scores[key] * weights[key] for key in weights)
        
        return {
            **base_scores,
            "total": round(total_score, 1),
            "notes": f"Interview completed on {interview_link.created_at.strftime('%Y-%m-%d %H:%M')}"
        }
        
    except Exception as e:
        logger.error(f"Failed to calculate interview scores: {e}")
        return {
            "technical": 0,
            "communication": 0,
            "cultural_fit": 0,
            "problem_solving": 0,
            "total": 0,
            "notes": "Error calculating scores"
        }

async def generate_recommendation(scores: Dict[str, Any], application: models.Application) -> str:
    """Generate AI-powered hiring recommendation."""
    try:
        prompt = f"""
        Based on the following interview scores and application data, provide a hiring recommendation.
        
        Interview Scores:
        - Technical: {scores.get('technical', 0)}/100
        - Communication: {scores.get('communication', 0)}/100
        - Cultural Fit: {scores.get('cultural_fit', 0)}/100
        - Problem Solving: {scores.get('problem_solving', 0)}/100
        - Total: {scores.get('total', 0)}/100
        
        Application Data:
        - Job: {application.job.title}
        - Match Score: {application.match_score or 'N/A'}
        - Candidate: {application.candidate.name}
        
        Provide one of these recommendations: SELECT, REJECT, or MAYBE.
        Also provide a brief reasoning (1-2 sentences).
        
        Format your response as: RECOMMENDATION: [SELECT/REJECT/MAYBE] | REASONING: [brief explanation]
        """
        
        response = await ai_service.openai.ChatCompletion.acreate(
            model=ai_service.chat_model,
            messages=[
                {"role": "system", "content": "You are an expert HR professional providing hiring recommendations based on interview scores."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.3
        )
        
        recommendation_text = response.choices[0].message.content.strip()
        
        # Extract recommendation
        if "SELECT" in recommendation_text.upper():
            return "SELECT"
        elif "REJECT" in recommendation_text.upper():
            return "REJECT"
        else:
            return "MAYBE"
            
    except Exception as e:
        logger.error(f"Failed to generate AI recommendation: {e}")
        # Fallback logic
        total_score = scores.get("total", 0)
        if total_score >= 80:
            return "SELECT"
        elif total_score >= 60:
            return "MAYBE"
        else:
            return "REJECT"
