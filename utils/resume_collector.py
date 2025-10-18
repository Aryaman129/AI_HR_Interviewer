"""
Resume collector utility to gather sample resumes for demonstration
"""

import requests
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
import time
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResumeCollector:
    def __init__(self):
        """Initialize the resume collector"""
        self.sample_resumes = []
        self.output_dir = Path("backend/data/resumes")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_sample_resumes(self) -> List[Dict[str, Any]]:
        """Generate diverse sample resumes for demonstration"""
        
        # Sample resume templates for different roles and experience levels
        resume_templates = [
            {
                "name": "John_Smith_Senior_Software_Engineer",
                "role": "Senior Software Engineer",
                "experience_years": 8,
                "content": """
JOHN SMITH
Senior Software Engineer
Email: john.smith@email.com | Phone: (555) 123-4567
LinkedIn: linkedin.com/in/johnsmith | GitHub: github.com/johnsmith

PROFESSIONAL SUMMARY
Experienced Senior Software Engineer with 8+ years of expertise in full-stack development, 
cloud architecture, and team leadership. Proven track record of delivering scalable solutions 
using modern technologies and agile methodologies.

TECHNICAL SKILLS
• Programming Languages: Python, Java, JavaScript, TypeScript, C++
• Frameworks: React, Node.js, Django, Spring Boot, Express.js
• Cloud Platforms: AWS (EC2, S3, Lambda, RDS), Azure, Docker, Kubernetes
• Databases: PostgreSQL, MongoDB, Redis, MySQL
• Tools: Git, Jenkins, JIRA, Confluence, VS Code

PROFESSIONAL EXPERIENCE

Senior Software Engineer | TechCorp Inc. | 2020 - Present
• Led development of microservices architecture serving 1M+ users
• Implemented CI/CD pipelines reducing deployment time by 60%
• Mentored 5 junior developers and conducted code reviews
• Designed and built RESTful APIs with 99.9% uptime
• Collaborated with product managers to define technical requirements

Software Engineer | StartupXYZ | 2018 - 2020
• Developed responsive web applications using React and Node.js
• Optimized database queries improving application performance by 40%
• Integrated third-party APIs and payment gateways
• Participated in agile development cycles and sprint planning

Junior Software Developer | DevSolutions | 2016 - 2018
• Built web applications using Python Django framework
• Wrote unit tests achieving 85% code coverage
• Fixed bugs and implemented new features based on user feedback
• Collaborated with QA team to ensure software quality

EDUCATION
Bachelor of Science in Computer Science
University of Technology | 2012 - 2016
GPA: 3.7/4.0

CERTIFICATIONS
• AWS Certified Solutions Architect - Associate (2021)
• Certified Scrum Master (2020)

PROJECTS
E-commerce Platform (2021)
• Built scalable e-commerce platform using React, Node.js, and AWS
• Implemented secure payment processing and inventory management
• Achieved 99.5% uptime with auto-scaling infrastructure

ACHIEVEMENTS
• Reduced system latency by 50% through performance optimization
• Led successful migration of legacy system to cloud infrastructure
• Received "Employee of the Year" award in 2021
"""
            },
            {
                "name": "Sarah_Johnson_Cybersecurity_Specialist",
                "role": "Cybersecurity Specialist",
                "experience_years": 5,
                "content": """
SARAH JOHNSON
Cybersecurity Specialist
Email: sarah.johnson@email.com | Phone: (555) 987-6543
LinkedIn: linkedin.com/in/sarahjohnson

PROFESSIONAL SUMMARY
Dedicated Cybersecurity Specialist with 5+ years of experience in threat analysis, 
vulnerability assessment, and security incident response. Expert in implementing 
security frameworks and protecting critical infrastructure.

TECHNICAL SKILLS
• Security Frameworks: NIST, ISO 27001, OWASP, CIS Controls
• Security Tools: Wireshark, Nessus, Metasploit, Burp Suite, Splunk
• Programming: Python, PowerShell, Bash, C++, SQL
• Operating Systems: Windows, Linux (Ubuntu, CentOS), macOS
• Cloud Security: AWS Security, Azure Security Center, GCP Security

PROFESSIONAL EXPERIENCE

Cybersecurity Specialist | SecureBank Corp | 2021 - Present
• Conducted vulnerability assessments and penetration testing
• Implemented security monitoring using SIEM tools (Splunk, QRadar)
• Responded to 50+ security incidents with average resolution time of 2 hours
• Developed security policies and procedures for compliance (SOX, PCI-DSS)
• Trained 100+ employees on cybersecurity best practices

Information Security Analyst | TechGuard Solutions | 2019 - 2021
• Monitored network traffic for suspicious activities and threats
• Performed risk assessments and created mitigation strategies
• Implemented multi-factor authentication reducing security breaches by 80%
• Collaborated with IT teams to secure cloud infrastructure
• Maintained security documentation and incident reports

Junior Security Analyst | CyberDefense Inc | 2018 - 2019
• Analyzed security logs and identified potential threats
• Assisted in forensic investigations of security incidents
• Updated antivirus signatures and security patches
• Supported security awareness training programs

EDUCATION
Bachelor of Science in Cybersecurity
Cyber University | 2014 - 2018
Relevant Coursework: Network Security, Ethical Hacking, Digital Forensics

CERTIFICATIONS
• Certified Information Systems Security Professional (CISSP) - 2022
• Certified Ethical Hacker (CEH) - 2021
• CompTIA Security+ - 2020
• AWS Certified Security - Specialty - 2021

PROJECTS
Network Security Assessment (2022)
• Led comprehensive security assessment for Fortune 500 company
• Identified 25 critical vulnerabilities and provided remediation plan
• Implemented security controls reducing risk exposure by 70%

ACHIEVEMENTS
• Detected and prevented advanced persistent threat (APT) attack
• Reduced false positive alerts by 60% through tuning SIEM rules
• Achieved 100% compliance in annual security audits
"""
            },
            {
                "name": "Mike_Chen_Data_Scientist",
                "role": "Data Scientist",
                "experience_years": 4,
                "content": """
MIKE CHEN
Data Scientist
Email: mike.chen@email.com | Phone: (555) 456-7890
LinkedIn: linkedin.com/in/mikechen | GitHub: github.com/mikechen

PROFESSIONAL SUMMARY
Results-driven Data Scientist with 4+ years of experience in machine learning, 
statistical analysis, and data visualization. Proven ability to extract actionable 
insights from complex datasets and drive business decisions.

TECHNICAL SKILLS
• Programming Languages: Python, R, SQL, Scala, Java
• Machine Learning: Scikit-learn, TensorFlow, PyTorch, Keras, XGBoost
• Data Visualization: Tableau, Power BI, Matplotlib, Seaborn, Plotly
• Big Data: Spark, Hadoop, Kafka, Airflow
• Cloud Platforms: AWS (SageMaker, EMR), GCP (BigQuery, Vertex AI)
• Databases: PostgreSQL, MongoDB, Cassandra, Snowflake

PROFESSIONAL EXPERIENCE

Data Scientist | DataTech Analytics | 2021 - Present
• Developed machine learning models improving customer retention by 25%
• Built recommendation system increasing revenue by $2M annually
• Implemented A/B testing framework for product optimization
• Created automated reporting dashboards using Tableau and Python
• Collaborated with cross-functional teams to define KPIs and metrics

Junior Data Scientist | InsightCorp | 2020 - 2021
• Analyzed customer behavior data to identify growth opportunities
• Built predictive models for demand forecasting with 90% accuracy
• Performed statistical analysis and hypothesis testing
• Created data pipelines for real-time analytics
• Presented findings to stakeholders and executive leadership

Data Analyst | StartupAnalytics | 2019 - 2020
• Cleaned and processed large datasets using Python and SQL
• Created interactive dashboards for business intelligence
• Conducted exploratory data analysis to identify trends
• Supported marketing campaigns with data-driven insights
• Automated reporting processes reducing manual work by 70%

EDUCATION
Master of Science in Data Science
Data Science University | 2017 - 2019
Thesis: "Deep Learning for Time Series Forecasting"

Bachelor of Science in Statistics
Statistics College | 2013 - 2017
GPA: 3.8/4.0

CERTIFICATIONS
• AWS Certified Machine Learning - Specialty (2022)
• Google Cloud Professional Data Engineer (2021)
• Tableau Desktop Specialist (2020)

PROJECTS
Customer Churn Prediction (2022)
• Developed ensemble model predicting customer churn with 92% accuracy
• Implemented feature engineering and hyperparameter tuning
• Deployed model to production using AWS SageMaker

Stock Price Prediction (2021)
• Built LSTM neural network for stock price forecasting
• Achieved 15% improvement over baseline models
• Created real-time prediction dashboard

ACHIEVEMENTS
• Reduced customer acquisition cost by 30% through predictive modeling
• Published research paper on "Machine Learning in Finance" (2021)
• Won company hackathon for innovative data solution (2022)
"""
            },
            {
                "name": "Emily_Davis_Frontend_Developer",
                "role": "Frontend Developer",
                "experience_years": 3,
                "content": """
EMILY DAVIS
Frontend Developer
Email: emily.davis@email.com | Phone: (555) 321-0987
LinkedIn: linkedin.com/in/emilydavis | Portfolio: emilydavis.dev

PROFESSIONAL SUMMARY
Creative Frontend Developer with 3+ years of experience building responsive, 
user-friendly web applications. Passionate about creating intuitive user interfaces 
and optimizing user experience across all devices.

TECHNICAL SKILLS
• Frontend: HTML5, CSS3, JavaScript (ES6+), TypeScript
• Frameworks/Libraries: React, Vue.js, Angular, Next.js, Nuxt.js
• Styling: Sass, Less, Styled Components, Tailwind CSS, Bootstrap
• Tools: Webpack, Vite, Babel, ESLint, Prettier
• Version Control: Git, GitHub, GitLab
• Testing: Jest, Cypress, React Testing Library

PROFESSIONAL EXPERIENCE

Frontend Developer | WebSolutions Inc | 2022 - Present
• Developed responsive web applications using React and TypeScript
• Implemented modern UI/UX designs with 98% client satisfaction rate
• Optimized application performance reducing load times by 40%
• Collaborated with designers and backend developers in agile environment
• Mentored 2 junior developers on frontend best practices

Junior Frontend Developer | DigitalAgency | 2021 - 2022
• Built interactive websites using Vue.js and modern CSS frameworks
• Converted design mockups to pixel-perfect responsive layouts
• Implemented accessibility features following WCAG guidelines
• Participated in code reviews and maintained coding standards
• Fixed cross-browser compatibility issues

Web Developer Intern | TechStartup | 2020 - 2021
• Assisted in developing company website using HTML, CSS, and JavaScript
• Created reusable UI components for design system
• Performed website testing and bug fixes
• Learned modern development workflows and tools

EDUCATION
Bachelor of Science in Computer Science
Web Development University | 2017 - 2021
Relevant Coursework: Web Development, Human-Computer Interaction, Database Systems

CERTIFICATIONS
• React Developer Certification (2022)
• Google UX Design Certificate (2021)

PROJECTS
E-learning Platform (2023)
• Built responsive learning platform using React and Node.js
• Implemented video streaming and interactive quizzes
• Achieved 95% user satisfaction in usability testing

Portfolio Website (2022)
• Designed and developed personal portfolio using Next.js
• Implemented dark/light theme toggle and smooth animations
• Optimized for SEO and accessibility

ACHIEVEMENTS
• Improved website conversion rate by 35% through UX optimization
• Reduced bundle size by 50% through code splitting and optimization
• Received "Rising Star" award for outstanding performance (2023)
"""
            },
            {
                "name": "Robert_Wilson_DevOps_Engineer",
                "role": "DevOps Engineer",
                "experience_years": 6,
                "content": """
ROBERT WILSON
DevOps Engineer
Email: robert.wilson@email.com | Phone: (555) 654-3210
LinkedIn: linkedin.com/in/robertwilson

PROFESSIONAL SUMMARY
Experienced DevOps Engineer with 6+ years of expertise in cloud infrastructure, 
automation, and continuous integration/deployment. Proven track record of 
improving system reliability and reducing deployment times.

TECHNICAL SKILLS
• Cloud Platforms: AWS, Azure, Google Cloud Platform
• Containerization: Docker, Kubernetes, OpenShift
• Infrastructure as Code: Terraform, CloudFormation, Ansible
• CI/CD: Jenkins, GitLab CI, GitHub Actions, Azure DevOps
• Monitoring: Prometheus, Grafana, ELK Stack, Datadog
• Scripting: Bash, Python, PowerShell, Go

PROFESSIONAL EXPERIENCE

Senior DevOps Engineer | CloudTech Solutions | 2021 - Present
• Designed and implemented cloud infrastructure for 50+ applications
• Reduced deployment time from 2 hours to 15 minutes using CI/CD pipelines
• Implemented monitoring and alerting systems achieving 99.9% uptime
• Led migration of legacy applications to Kubernetes clusters
• Automated infrastructure provisioning saving 20 hours/week

DevOps Engineer | ScaleUp Inc | 2019 - 2021
• Built and maintained CI/CD pipelines for microservices architecture
• Implemented Infrastructure as Code using Terraform and Ansible
• Set up monitoring and logging solutions for production systems
• Collaborated with development teams to optimize application performance
• Managed AWS infrastructure serving 500K+ daily active users

Systems Administrator | TechCorp | 2018 - 2019
• Administered Linux and Windows servers in hybrid cloud environment
• Implemented backup and disaster recovery procedures
• Automated routine tasks using shell scripts and Python
• Maintained network security and access controls
• Provided 24/7 on-call support for critical systems

EDUCATION
Bachelor of Science in Information Technology
Tech University | 2014 - 2018
Relevant Coursework: Network Administration, Cloud Computing, System Security

CERTIFICATIONS
• AWS Certified Solutions Architect - Professional (2022)
• Certified Kubernetes Administrator (CKA) - 2021
• HashiCorp Certified: Terraform Associate (2021)
• Azure DevOps Engineer Expert (2020)

PROJECTS
Multi-Cloud Infrastructure (2022)
• Designed hybrid cloud architecture spanning AWS and Azure
• Implemented disaster recovery with 99.99% availability SLA
• Reduced infrastructure costs by 30% through optimization

Microservices Migration (2021)
• Led migration of monolithic application to microservices
• Implemented service mesh using Istio for traffic management
• Achieved 50% improvement in deployment frequency

ACHIEVEMENTS
• Reduced infrastructure costs by $100K annually through optimization
• Improved system reliability from 95% to 99.9% uptime
• Implemented zero-downtime deployment strategy
• Received "Technical Excellence" award (2022)
"""
            }
        ]
        
        # Generate resume files
        for template in resume_templates:
            filename = f"{template['name']}.txt"
            filepath = self.output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(template['content'])
            
            logger.info(f"Generated sample resume: {filename}")
        
        logger.info(f"Generated {len(resume_templates)} sample resumes in {self.output_dir}")
        return resume_templates
    
    def create_job_requirements_samples(self):
        """Create sample job requirements for testing"""
        job_samples = [
            {
                "role": "Senior Software Engineer",
                "required_skills": ["Python", "JavaScript", "React", "AWS", "Docker"],
                "preferred_skills": ["Kubernetes", "TypeScript", "PostgreSQL", "Redis"],
                "min_experience_years": 5,
                "education_level": "Bachelor",
                "location": "Remote",
                "description": "We are looking for a Senior Software Engineer to join our growing team..."
            },
            {
                "role": "Cybersecurity Specialist",
                "required_skills": ["Network Security", "SIEM", "Python", "Linux", "Incident Response"],
                "preferred_skills": ["CISSP", "CEH", "Penetration Testing", "Cloud Security"],
                "min_experience_years": 3,
                "education_level": "Bachelor",
                "location": "New York",
                "description": "Join our cybersecurity team to protect critical infrastructure..."
            },
            {
                "role": "Data Scientist",
                "required_skills": ["Python", "Machine Learning", "SQL", "Statistics", "Pandas"],
                "preferred_skills": ["TensorFlow", "AWS", "Tableau", "R", "Deep Learning"],
                "min_experience_years": 2,
                "education_level": "Master",
                "location": "San Francisco",
                "description": "We need a Data Scientist to help us make data-driven decisions..."
            }
        ]
        
        # Save job requirements
        jobs_file = Path("config/sample_jobs.json")
        with open(jobs_file, 'w') as f:
            json.dump(job_samples, f, indent=2)
        
        logger.info(f"Created sample job requirements: {jobs_file}")
        return job_samples

if __name__ == "__main__":
    collector = ResumeCollector()
    collector.generate_sample_resumes()
    collector.create_job_requirements_samples()
    print("Sample resumes and job requirements generated successfully!")
