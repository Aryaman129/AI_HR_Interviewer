"""
Bias Detection Service

Dual-layer bias detection system:
1. Rule-based: Pattern matching for 7 protected categories
2. LLM-based: Subtle bias detection using AI analysis

Detects bias in:
- Interview questions
- Job descriptions
- Candidate evaluations
- Screening feedback
"""

from typing import List, Dict, Any, Optional, Set
from enum import Enum
import re
import logging
from dataclasses import dataclass

from app.services.llm_provider import get_llm_service, LLMOptions

logger = logging.getLogger(__name__)


class BiasCategory(str, Enum):
    """Protected categories for bias detection"""
    GENDER = "gender"
    AGE = "age"
    RACE = "race"
    DISABILITY = "disability"
    RELIGION = "religion"
    NATIONALITY = "nationality"
    FAMILY_STATUS = "family_status"


@dataclass
class BiasDetection:
    """Single bias detection result"""
    category: BiasCategory
    severity: str  # "low", "medium", "high"
    text_snippet: str
    explanation: str
    suggestion: str
    detection_method: str  # "rule_based" or "llm_based"
    confidence: float  # 0.0 to 1.0


class BiasDetector:
    """
    Dual-layer bias detection system for fair hiring.
    
    Features:
    - Rule-based pattern matching (fast, high precision)
    - LLM-based analysis (slower, catches subtle bias)
    - Combined detection with deduplication
    - Audit logging for compliance
    """
    
    # Rule-based patterns for each category
    BIAS_PATTERNS = {
        BiasCategory.GENDER: [
            r'\b(he|she|his|her|him)\b',
            r'\b(male|female|man|woman|boy|girl|gentleman|lady)\b',
            r'\b(manpower|mankind|man-hours)\b',
            r'\b(guys|gals|dude|chick)\b',
            r'\b(motherhood|fatherhood|pregnant|maternity|paternity)\b',
        ],
        BiasCategory.AGE: [
            r'\b(young|old|elderly|senior|junior|mature|youthful|aging)\b',
            r'\b(recent graduate|new grad|digital native)\b',
            r'\b(years? of birth|age|date of birth)\b',
            r'\b(retirement|retiree)\b',
        ],
        BiasCategory.RACE: [
            r'\b(race|ethnicity|ethnic|cultural background|national origin)\b',
            r'\b(white|black|asian|hispanic|latino|caucasian|african|european)\b',
            r'\b(native speaker|fluent english speaker)\b',
            r'\b(diversity hire|minority)\b',
        ],
        BiasCategory.DISABILITY: [
            r'\b(disabled|disability|handicap|able-bodied|wheelchair)\b',
            r'\b(blind|deaf|mute|lame|crippled)\b',
            r'\b(mental health|psychiatric|psychological condition)\b',
            r'\b(medical condition|health status)\b',
        ],
        BiasCategory.RELIGION: [
            r'\b(religion|religious|faith|belief|spiritual)\b',
            r'\b(christian|muslim|jewish|hindu|buddhist|atheist)\b',
            r'\b(church|mosque|temple|synagogue)\b',
            r'\b(prayer|worship|sabbath|holiday observance)\b',
        ],
        BiasCategory.NATIONALITY: [
            r'\b(citizen|citizenship|visa status|work permit|green card)\b',
            r'\b(immigrant|foreign|native|local)\b',
            r'\b(accent|nationality|country of origin)\b',
            r'\b(english as second language|ESL)\b',
        ],
        BiasCategory.FAMILY_STATUS: [
            r'\b(married|single|divorced|widowed|marital status)\b',
            r'\b(children|kids|family|spouse|partner|husband|wife)\b',
            r'\b(childcare|parental|family obligations)\b',
            r'\b(pregnancy|expecting|planning a family)\b',
        ]
    }
    
    def __init__(self):
        """Initialize bias detector with LLM service"""
        self.llm_service = get_llm_service()
    
    def detect_bias_rule_based(self, text: str) -> List[BiasDetection]:
        """
        Rule-based bias detection using pattern matching.
        
        Args:
            text: Text to analyze (question, description, feedback)
        
        Returns:
            List of BiasDetection objects
        
        Example:
            detections = detector.detect_bias_rule_based(
                "Are you planning to have children in the next few years?"
            )
            # Returns: [BiasDetection(category=FAMILY_STATUS, ...)]
        """
        detections = []
        text_lower = text.lower()
        
        for category, patterns in self.BIAS_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text_lower, re.IGNORECASE)
                for match in matches:
                    snippet = self._extract_snippet(text, match.start(), match.end())
                    
                    detection = BiasDetection(
                        category=category,
                        severity=self._assess_severity(category, match.group()),
                        text_snippet=snippet,
                        explanation=f"Detected {category.value} bias: '{match.group()}'",
                        suggestion=self._get_suggestion(category, match.group()),
                        detection_method="rule_based",
                        confidence=0.9  # High confidence for pattern matches
                    )
                    detections.append(detection)
        
        logger.info(f"Rule-based: Found {len(detections)} bias indicators")
        return detections
    
    async def detect_bias_llm(self, text: str) -> List[BiasDetection]:
        """
        LLM-based bias detection for subtle biases.
        
        Args:
            text: Text to analyze
        
        Returns:
            List of BiasDetection objects
        
        Example:
            detections = await detector.detect_bias_llm(
                "We're looking for someone who can keep up with our fast-paced environment"
            )
            # May detect age bias (subtle "young person" implication)
        """
        prompt = f"""Analyze the following text for potential hiring bias across these protected categories:
1. Gender
2. Age
3. Race/Ethnicity
4. Disability
5. Religion
6. Nationality
7. Family Status

TEXT TO ANALYZE:
\"\"\"{text}\"\"\"

Look for:
- Direct references to protected categories
- Subtle language that may exclude certain groups
- Implicit assumptions or stereotypes
- Coded language or dog whistles

Return ONLY valid JSON in this format:
{{
    "biases": [
        {{
            "category": "gender|age|race|disability|religion|nationality|family_status",
            "severity": "low|medium|high",
            "text_snippet": "exact quoted text showing bias",
            "explanation": "why this is biased",
            "suggestion": "how to rephrase",
            "confidence": 0.0-1.0
        }}
    ]
}}

If no bias detected, return: {{"biases": []}}
"""
        
        try:
            options = LLMOptions(
                temperature=0.3,  # Low temp for consistent detection
                max_tokens=1000,
                response_format="json"
            )
            
            llm_response = await self.llm_service.generate(prompt, options)
            
            if llm_response and llm_response.content:
                import json
                result = json.loads(llm_response.content)
                
                detections = []
                for bias in result.get("biases", []):
                    detection = BiasDetection(
                        category=BiasCategory(bias["category"]),
                        severity=bias["severity"],
                        text_snippet=bias["text_snippet"],
                        explanation=bias["explanation"],
                        suggestion=bias["suggestion"],
                        detection_method="llm_based",
                        confidence=bias.get("confidence", 0.7)
                    )
                    detections.append(detection)
                
                logger.info(f"LLM-based: Found {len(detections)} bias indicators using {llm_response.provider}")
                return detections
            
            return []
            
        except Exception as e:
            logger.error(f"LLM bias detection failed: {str(e)}")
            return []
    
    async def detect_bias(self, text: str, use_llm: bool = True) -> List[BiasDetection]:
        """
        Combined bias detection (rule-based + LLM).
        
        Args:
            text: Text to analyze
            use_llm: Whether to include LLM-based detection (default True)
        
        Returns:
            Deduplicated list of BiasDetection objects
        
        Example:
            detections = await detector.detect_bias(
                "We need an energetic recent graduate who is a native English speaker"
            )
            # Returns detections for age, nationality bias
        """
        # Always run rule-based (fast)
        rule_detections = self.detect_bias_rule_based(text)
        
        if not use_llm:
            return rule_detections
        
        # Run LLM-based for subtle biases
        llm_detections = await self.detect_bias_llm(text)
        
        # Combine and deduplicate
        all_detections = rule_detections + llm_detections
        deduplicated = self._deduplicate_detections(all_detections)
        
        logger.info(f"Combined: {len(deduplicated)} unique biases detected")
        return deduplicated
    
    def _extract_snippet(self, text: str, start: int, end: int, context_chars: int = 50) -> str:
        """Extract text snippet with context around match"""
        snippet_start = max(0, start - context_chars)
        snippet_end = min(len(text), end + context_chars)
        return "..." + text[snippet_start:snippet_end].strip() + "..."
    
    def _assess_severity(self, category: BiasCategory, matched_text: str) -> str:
        """Assess severity of bias (low/medium/high)"""
        # Direct protected category references are high severity
        high_severity_terms = [
            "age", "race", "religion", "disability", "pregnant", "married",
            "citizenship", "visa", "gender", "ethnicity"
        ]
        
        if any(term in matched_text.lower() for term in high_severity_terms):
            return "high"
        
        # Gendered pronouns are medium
        if category == BiasCategory.GENDER and matched_text.lower() in ["he", "she", "his", "her"]:
            return "medium"
        
        return "low"
    
    def _get_suggestion(self, category: BiasCategory, matched_text: str) -> str:
        """Get suggestion for neutral phrasing"""
        suggestions = {
            BiasCategory.GENDER: "Use gender-neutral terms (they/them, person, candidate)",
            BiasCategory.AGE: "Focus on experience and skills, not age",
            BiasCategory.RACE: "Remove references to race, ethnicity, or national origin",
            BiasCategory.DISABILITY: "Focus on job requirements, not physical abilities",
            BiasCategory.RELIGION: "Remove religious references unless bona fide requirement",
            BiasCategory.NATIONALITY: "Remove citizenship/visa requirements unless legally required",
            BiasCategory.FAMILY_STATUS: "Remove family/marital status questions"
        }
        return suggestions.get(category, "Rephrase to focus on job requirements")
    
    def _deduplicate_detections(self, detections: List[BiasDetection]) -> List[BiasDetection]:
        """Remove duplicate detections (prefer higher confidence)"""
        # Group by category + text_snippet
        grouped: Dict[tuple, List[BiasDetection]] = {}
        
        for detection in detections:
            key = (detection.category, detection.text_snippet[:50])  # First 50 chars
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(detection)
        
        # Keep highest confidence detection from each group
        deduplicated = []
        for group in grouped.values():
            best = max(group, key=lambda d: d.confidence)
            deduplicated.append(best)
        
        return deduplicated
