"""
Integration Test Suite for AI-HR Platform
Tests all major components and workflows
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from app.db.database import engine, get_db, SessionLocal
from app.core.config import settings
import httpx

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


class TestRunner:
    """Runs integration tests for the AI-HR platform"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        
    def print_header(self, text: str):
        """Print section header"""
        print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
        print(f"{BOLD}{BLUE}{text.center(60)}{RESET}")
        print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")
        
    def print_test(self, name: str, passed: bool, message: str = ""):
        """Print test result"""
        if passed:
            print(f"{GREEN}✓{RESET} {name}")
            if message:
                print(f"  {message}")
            self.passed += 1
        else:
            print(f"{RED}✗{RESET} {name}")
            if message:
                print(f"  {RED}{message}{RESET}")
            self.failed += 1
            
    def print_warning(self, name: str, message: str):
        """Print warning"""
        print(f"{YELLOW}⚠{RESET} {name}")
        if message:
            print(f"  {YELLOW}{message}{RESET}")
        self.warnings += 1
        
    def print_summary(self):
        """Print test summary"""
        total = self.passed + self.failed
        print(f"\n{BOLD}{'='*60}{RESET}")
        print(f"{BOLD}TEST SUMMARY{RESET}")
        print(f"{BOLD}{'='*60}{RESET}")
        print(f"{GREEN}Passed:{RESET} {self.passed}/{total}")
        print(f"{RED}Failed:{RESET} {self.failed}/{total}")
        print(f"{YELLOW}Warnings:{RESET} {self.warnings}")
        
        if self.failed == 0:
            print(f"\n{GREEN}{BOLD}🎉 ALL TESTS PASSED!{RESET}\n")
        else:
            print(f"\n{RED}{BOLD}❌ SOME TESTS FAILED{RESET}\n")
            
        return self.failed == 0


async def test_database_connection(runner: TestRunner):
    """Test 1: Database connectivity"""
    runner.print_header("TEST 1: DATABASE CONNECTIVITY")
    
    try:
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            runner.print_test(
                "PostgreSQL connection",
                True,
                f"Connected to: {version[:50]}..."
            )
    except Exception as e:
        runner.print_test("PostgreSQL connection", False, str(e))
        return False
        
    # Test pgvector extension
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
            ext = result.fetchone()
            if ext:
                runner.print_test("pgvector extension", True, "Extension installed and active")
            else:
                runner.print_test("pgvector extension", False, "Extension not found")
    except Exception as e:
        runner.print_test("pgvector extension", False, str(e))
        
    # Test database exists
    try:
        db = SessionLocal()
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        expected_tables = [
            'candidates', 'jobs', 'resumes', 'applications', 
            'screenings', 'interviews', 'users', 'feedbacks', 'audit_logs'
        ]
        
        existing = [t for t in expected_tables if t in tables]
        missing = [t for t in expected_tables if t not in tables]
        
        if len(existing) == len(expected_tables):
            runner.print_test(
                "Database schema", 
                True, 
                f"All {len(expected_tables)} tables exist"
            )
        else:
            runner.print_warning(
                "Database schema",
                f"Found {len(existing)}/{len(expected_tables)} tables. Missing: {missing}"
            )
            
        # Check for vector columns
        if 'candidates' in tables:
            columns = inspector.get_columns('candidates')
            vector_cols = [c for c in columns if 'vector' in str(c.get('type')).lower()]
            if vector_cols:
                runner.print_test(
                    "pgvector columns",
                    True,
                    f"Found vector columns: {[c['name'] for c in vector_cols]}"
                )
            else:
                runner.print_warning(
                    "pgvector columns",
                    "No vector columns found in candidates table"
                )
                
        db.close()
        
    except Exception as e:
        runner.print_test("Database schema inspection", False, str(e))
        
    return True


async def test_dependencies(runner: TestRunner):
    """Test 2: Python dependencies"""
    runner.print_header("TEST 2: PYTHON DEPENDENCIES")
    
    dependencies = [
        ("fastapi", "FastAPI web framework"),
        ("sqlalchemy", "Database ORM"),
        ("pydantic", "Data validation"),
        ("transformers", "HuggingFace transformers"),
        ("sentence_transformers", "Sentence embeddings"),
        ("spacy", "NLP library"),
        ("sklearn", "Scikit-learn for ML"),
        ("ollama", "Ollama client"),
        ("httpx", "HTTP client"),
        ("aiohttp", "Async HTTP client"),
    ]
    
    for module_name, description in dependencies:
        try:
            __import__(module_name)
            runner.print_test(f"{module_name}", True, description)
        except ImportError as e:
            runner.print_test(f"{module_name}", False, f"Import failed: {str(e)}")
            
    # Test spaCy model
    try:
        import spacy
        nlp = spacy.load(settings.SPACY_MODEL)
        runner.print_test(
            f"spaCy model ({settings.SPACY_MODEL})",
            True,
            f"Model loaded successfully"
        )
    except Exception as e:
        runner.print_warning(
            f"spaCy model ({settings.SPACY_MODEL})",
            f"Not loaded: {str(e)}"
        )
        
    # Test sentence transformers model
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(settings.SENTENCE_TRANSFORMER_MODEL)
        runner.print_test(
            "Sentence transformer model",
            True,
            f"Model: {settings.SENTENCE_TRANSFORMER_MODEL}"
        )
    except Exception as e:
        runner.print_warning(
            "Sentence transformer model",
            f"Not loaded: {str(e)}"
        )


async def test_services(runner: TestRunner):
    """Test 3: Service imports and initialization"""
    runner.print_header("TEST 3: SERVICE IMPORTS")
    
    services = [
        ("app.services.resume_parser", "ResumeParser"),
        ("app.services.job_matcher", "JobCandidateMatchingService"),
        ("app.services.ai_screening", "AIScreeningService"),
    ]
    
    for module_path, class_name in services:
        try:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            runner.print_test(
                f"{class_name}",
                True,
                f"Imported from {module_path}"
            )
        except Exception as e:
            runner.print_test(
                f"{class_name}",
                False,
                f"Import failed: {str(e)}"
            )


async def test_models(runner: TestRunner):
    """Test 4: Database models"""
    runner.print_header("TEST 4: DATABASE MODELS")
    
    models = [
        "Candidate", "Job", "Resume", "Application", 
        "Screening", "Interview", "User", "Feedback", "AuditLog"
    ]
    
    for model_name in models:
        try:
            module = __import__("app.models", fromlist=[model_name])
            model_cls = getattr(module, model_name)
            runner.print_test(
                f"{model_name} model",
                True,
                f"Table: {model_cls.__tablename__}"
            )
        except Exception as e:
            runner.print_test(
                f"{model_name} model",
                False,
                f"Import failed: {str(e)}"
            )


async def test_api_endpoints(runner: TestRunner):
    """Test 5: API endpoints availability"""
    runner.print_header("TEST 5: API ENDPOINTS (require running server)")
    
    # Check if server is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health", timeout=2.0)
            if response.status_code == 200:
                runner.print_test("Backend server", True, "Server is running on port 8000")
                
                # Test endpoints
                endpoints = [
                    ("/", "Root endpoint"),
                    ("/docs", "OpenAPI docs"),
                    ("/api/v1/info", "API info"),
                ]
                
                for path, description in endpoints:
                    try:
                        response = await client.get(f"http://localhost:8000{path}")
                        runner.print_test(
                            f"GET {path}",
                            response.status_code == 200,
                            f"{description} - Status: {response.status_code}"
                        )
                    except Exception as e:
                        runner.print_test(f"GET {path}", False, str(e))
                        
            else:
                runner.print_warning(
                    "Backend server",
                    "Server responded but not healthy"
                )
    except Exception as e:
        runner.print_warning(
            "Backend server",
            f"Server not running: {str(e)}\nStart with: cd backend && python -m app.main"
        )


async def test_ollama_connection(runner: TestRunner):
    """Test 6: Ollama service"""
    runner.print_header("TEST 6: OLLAMA SERVICE")
    
    try:
        async with httpx.AsyncClient() as client:
            # Test Ollama connection
            response = await client.get(f"{settings.OLLAMA_HOST}/api/tags", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                model_names = [m['name'] for m in models]
                
                runner.print_test(
                    "Ollama service",
                    True,
                    f"Connected to {settings.OLLAMA_HOST}"
                )
                
                # Check if required model is available
                if any(settings.OLLAMA_MODEL in name for name in model_names):
                    runner.print_test(
                        f"Ollama model ({settings.OLLAMA_MODEL})",
                        True,
                        "Model is available"
                    )
                else:
                    runner.print_warning(
                        f"Ollama model ({settings.OLLAMA_MODEL})",
                        f"Model not found. Available: {model_names}\nRun: ollama pull {settings.OLLAMA_MODEL}"
                    )
            else:
                runner.print_test("Ollama service", False, f"Status: {response.status_code}")
    except Exception as e:
        runner.print_warning(
            "Ollama service",
            f"Not accessible: {str(e)}\nStart with: ollama serve"
        )


async def test_configuration(runner: TestRunner):
    """Test 7: Configuration"""
    runner.print_header("TEST 7: CONFIGURATION")
    
    # Check critical settings
    configs = [
        ("Database URL", settings.DATABASE_URL, "postgresql://"),
        ("Ollama host", settings.OLLAMA_HOST, "http://"),
        ("App name", settings.APP_NAME, None),
        ("API prefix", settings.API_V1_PREFIX, "/api/v1"),
    ]
    
    for name, value, expected_prefix in configs:
        if expected_prefix:
            is_valid = value.startswith(expected_prefix)
            runner.print_test(
                name,
                is_valid,
                f"Value: {value}" if is_valid else f"Invalid: {value}"
            )
        else:
            runner.print_test(name, bool(value), f"Value: {value}")
            
    # Check optional services
    optional = [
        ("Twilio", settings.TWILIO_ACCOUNT_SID),
        ("SendGrid", settings.SENDGRID_API_KEY),
        ("R2 Storage", settings.R2_ACCESS_KEY_ID),
    ]
    
    print(f"\n{BOLD}Optional Services:{RESET}")
    for name, value in optional:
        status = f"{GREEN}Configured{RESET}" if value else f"{YELLOW}Not configured{RESET}"
        print(f"  {name}: {status}")


async def main():
    """Run all tests"""
    print(f"\n{BOLD}{BLUE}╔════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{BLUE}║       AI-HR PLATFORM INTEGRATION TEST SUITE               ║{RESET}")
    print(f"{BOLD}{BLUE}╚════════════════════════════════════════════════════════════╝{RESET}\n")
    
    runner = TestRunner()
    
    # Run all test suites
    await test_configuration(runner)
    await test_database_connection(runner)
    await test_dependencies(runner)
    await test_models(runner)
    await test_services(runner)
    await test_ollama_connection(runner)
    await test_api_endpoints(runner)
    
    # Print summary
    success = runner.print_summary()
    
    # Return exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
