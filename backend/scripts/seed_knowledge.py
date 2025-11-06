"""
Seed Company Knowledge Script

Seeds the company_knowledge table with sample documents for testing RAG functionality.
Run this after applying migrations to populate initial company-specific context.

Usage:
    python backend/scripts/seed_knowledge.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.company_knowledge import CompanyKnowledge
from app.models.organization import Organization
from app.services.embedding_service import EmbeddingService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Sample company documents
SAMPLE_DOCUMENTS = [
    {
        "doc_type": "company_values",
        "title": "Core Engineering Values",
        "content": """
        At our company, we prioritize three core engineering values:
        
        1. **Code Quality**: We believe in writing clean, maintainable code with comprehensive test coverage.
           Every pull request undergoes rigorous code review.
        
        2. **Continuous Learning**: We encourage engineers to experiment with new technologies and share knowledge
           through tech talks, pair programming, and internal workshops.
        
        3. **Collaboration**: We work in cross-functional teams where engineers, designers, and product managers
           collaborate daily to build great products.
        """,
        "metadata": {"tags": ["culture", "engineering"], "author": "CTO"}
    },
    {
        "doc_type": "tech_requirements",
        "title": "Tech Stack Requirements",
        "content": """
        Our current technology stack includes:
        
        **Backend**: Python (FastAPI, Django), Node.js (Express, NestJS), PostgreSQL, Redis
        **Frontend**: React, TypeScript, Next.js, TailwindCSS
        **Infrastructure**: AWS (EC2, RDS, S3, Lambda), Docker, Kubernetes
        **Data**: Apache Airflow, dbt, Snowflake
        **CI/CD**: GitHub Actions, ArgoCD
        
        Candidates should have strong experience with at least 2 of our backend frameworks
        and be proficient in modern frontend development.
        """,
        "metadata": {"tags": ["tech_stack", "requirements"], "version": "2025"}
    },
    {
        "doc_type": "interview_style",
        "title": "Our Interview Process",
        "content": """
        We believe in a collaborative, respectful interview process:
        
        - **30-min Screening Call**: Culture fit and basic technical assessment
        - **60-min Technical Interview**: Live coding with emphasis on problem-solving approach, not just correct answer
        - **45-min System Design**: For senior roles, discuss scalability and architecture
        - **30-min Team Fit**: Meet potential team members, ask questions about day-to-day work
        
        We value candidates who:
        - Think out loud during problem-solving
        - Ask clarifying questions
        - Consider edge cases and trade-offs
        - Show curiosity about our tech stack and products
        """,
        "metadata": {"tags": ["interview", "process"], "updated": "2025-01"}
    },
    {
        "doc_type": "company_values",
        "title": "Diversity & Inclusion Commitment",
        "content": """
        We are committed to building a diverse and inclusive workplace:
        
        - **Equal Opportunity**: We evaluate candidates based on skills and experience, never on protected characteristics
        - **Bias-Free Hiring**: All interview questions focus on job-related competencies
        - **Accessibility**: We accommodate candidates with disabilities throughout the interview process
        - **Flexible Work**: Remote-first culture with flexible hours to support work-life balance
        - **Parental Support**: Generous parental leave and support for new parents
        """,
        "metadata": {"tags": ["DEI", "culture"], "importance": "high"}
    },
    {
        "doc_type": "tech_requirements",
        "title": "Senior Engineer Expectations",
        "content": """
        For senior engineering roles, we expect:
        
        **Technical Leadership**:
        - 5+ years professional software development
        - Experience leading projects from design to deployment
        - Strong system design and architecture skills
        - Expertise in at least one of our primary tech stacks
        
        **Collaboration**:
        - Mentor junior engineers
        - Participate in technical discussions and RFC reviews
        - Lead cross-team initiatives
        
        **Impact**:
        - Identify and solve complex technical problems
        - Make data-driven decisions
        - Contribute to engineering best practices
        """,
        "metadata": {"tags": ["senior", "requirements"], "level": "senior"}
    },
    {
        "doc_type": "company_values",
        "title": "Work-Life Balance Philosophy",
        "content": """
        We believe great work happens when people are well-rested and fulfilled:
        
        - No expectation of after-hours work unless critical incidents
        - Encourage taking full vacation time (20 days + national holidays)
        - Flexible hours - core hours 10am-3pm, otherwise flex
        - Remote work options for all roles
        - Mental health days encouraged
        - No "hustle culture" - sustainable pace over burnout
        """,
        "metadata": {"tags": ["culture", "benefits"], "priority": "high"}
    },
    {
        "doc_type": "tech_requirements",
        "title": "Quality & Testing Standards",
        "content": """
        Our quality standards:
        
        - **Test Coverage**: Minimum 80% for backend services, 70% for frontend
        - **Code Review**: All code reviewed by at least 2 engineers before merge
        - **CI/CD**: Automated tests run on every PR, deploy on merge to main
        - **Monitoring**: All services have metrics, logs, and alerts
        - **Documentation**: APIs documented with OpenAPI, architecture in Confluence
        
        Candidates should be comfortable with TDD/BDD practices and automated testing.
        """,
        "metadata": {"tags": ["quality", "testing"], "enforced": True}
    },
    {
        "doc_type": "interview_style",
        "title": "Coding Interview Guidelines",
        "content": """
        Our coding interviews focus on problem-solving, not memorization:
        
        - Candidates can use any programming language they're comfortable with
        - Access to documentation and Google is allowed (like real work!)
        - We care about thought process more than perfect syntax
        - Partial solutions are better than no solution
        - We ask follow-up questions to understand trade-offs
        
        Red flags we avoid:
        - Trick questions or brain teasers
        - Expecting perfect solutions in unrealistic timeframes
        - Testing obscure algorithms not used in daily work
        """,
        "metadata": {"tags": ["interview", "coding"], "philosophy": "practical"}
    },
    {
        "doc_type": "company_values",
        "title": "Customer-First Product Development",
        "content": """
        Our product development is driven by customer needs:
        
        - Engineers participate in customer discovery calls
        - We ship MVPs quickly and iterate based on feedback
        - Data analytics inform product decisions
        - Regular user testing before major releases
        - Cross-functional teams (eng, design, PM) work together from day 1
        
        We value engineers who are product-minded and care about user experience.
        """,
        "metadata": {"tags": ["product", "culture"], "core_value": True}
    },
    {
        "doc_type": "tech_requirements",
        "title": "Security & Compliance Requirements",
        "content": """
        Security is embedded in our development process:
        
        - SOC 2 Type II compliance maintained
        - Regular security training for all engineers
        - Dependency scanning and SAST in CI/CD pipeline
        - Secrets management with Vault/AWS Secrets Manager
        - GDPR and CCPA compliance for all user data
        
        Senior engineers should understand secure coding practices and common vulnerabilities (OWASP Top 10).
        """,
        "metadata": {"tags": ["security", "compliance"], "criticality": "high"}
    },
    {
        "doc_type": "interview_style",
        "title": "Behavioral Interview Focus",
        "content": """
        Our behavioral interviews assess:
        
        1. **Collaboration**: How do you work with teammates when there's disagreement?
        2. **Learning**: Tell us about a time you had to learn a new technology quickly
        3. **Impact**: Describe a project where you had significant technical impact
        4. **Failure**: Share a project that didn't go as planned and what you learned
        5. **Communication**: How do you explain technical concepts to non-technical stakeholders?
        
        We use the STAR method (Situation, Task, Action, Result) and value specific examples over generic answers.
        """,
        "metadata": {"tags": ["interview", "behavioral"], "framework": "STAR"}
    },
    {
        "doc_type": "company_values",
        "title": "Open Source Contribution Policy",
        "content": """
        We encourage open source participation:
        
        - Engineers can spend 10% of work time on open source contributions
        - We open-source our internal tools when possible
        - Conference attendance and speaking supported (budget + time off)
        - Active in Python, React, and DevOps communities
        
        Candidates with public GitHub profiles or OSS contributions are valued,
        but not required (we know many great engineers can't share code publicly).
        """,
        "metadata": {"tags": ["culture", "open_source"], "benefit": True}
    }
]


def seed_knowledge():
    """Seed company knowledge documents"""
    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Get first organization (assuming at least one exists)
        org = db.query(Organization).first()
        if not org:
            logger.error("No organization found! Please create an organization first.")
            return
        
        logger.info(f"Seeding knowledge for organization: {org.name}")
        
        # Initialize embedding service
        embedding_service = EmbeddingService()
        
        # Check if knowledge already exists
        existing_count = db.query(CompanyKnowledge).filter_by(organization_id=org.id).count()
        if existing_count > 0:
            logger.warning(f"Found {existing_count} existing documents. Skipping seed (delete manually if you want to reseed).")
            return
        
        # Create knowledge documents
        created_count = 0
        for doc_data in SAMPLE_DOCUMENTS:
            # Generate embedding
            embedding = embedding_service.generate_text_embedding(doc_data["content"])
            
            # Create document
            doc = CompanyKnowledge(
                organization_id=org.id,
                doc_type=doc_data["doc_type"],
                title=doc_data["title"],
                content=doc_data["content"],
                embedding=embedding,
                metadata=doc_data["metadata"]
            )
            db.add(doc)
            created_count += 1
            logger.info(f"  Created: {doc_data['title']} ({doc_data['doc_type']})")
        
        db.commit()
        logger.info(f"✅ Successfully seeded {created_count} company knowledge documents!")
        
        # Show summary
        by_type = {}
        for doc in SAMPLE_DOCUMENTS:
            doc_type = doc["doc_type"]
            by_type[doc_type] = by_type.get(doc_type, 0) + 1
        
        logger.info("\nSummary by type:")
        for doc_type, count in by_type.items():
            logger.info(f"  - {doc_type}: {count} documents")
        
    except Exception as e:
        logger.error(f"Error seeding knowledge: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Starting company knowledge seed...")
    seed_knowledge()
    logger.info("Done!")
