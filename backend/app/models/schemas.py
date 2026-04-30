from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class Severity(str, Enum): # Only these 4 values are allowed, anything else gets rejected
    critical = "Critical"
    high = "High"
    medium = "Medium"
    low = "Low"

class Risk(BaseModel):
    # ge = greater than or equal to 0
    # le = less than or equal to 100
    # score: "banana" or score: 999 → rejected instantly
    id: Optional[str] = None
    assessment_id: str
    title: str
    description: str
    severity: Severity
    score: int = Field(ge=0, le=100)
    category: str  # e.g. "AWS", "Network", "Application"
    remediation: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Assessment(BaseModel):
    id: Optional[str] = None
    company: str
    industry: str
    scope: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CopilotQuery(BaseModel):
    query: str # the question the user typed
    assessment_id: str # which assessment to pull risks from
    conversation_history: Optional[List[dict]] = [] # memory across turns

class CopilotResponse(BaseModel):
    answer: str # LLM's response
    risks_referenced: List[str] = [] # which risks were mentioned
    suggested_followups: List[str] = [] # next questions to show user