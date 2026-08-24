from __future__ import annotations

from typing import TypedDict


class RoleFamily(TypedDict):
    key: str
    label: str
    titles: list[str]
    keywords: list[str]


TECH_SKILLS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "golang", "ruby",
    "php", "kotlin", "swift", "scala", "r", "sql", "mysql", "postgresql", "mongodb",
    "redis", "oracle", "sqlite", "html", "css", "react", "angular", "vue", "next.js",
    "node.js", "express", "django", "flask", "fastapi", "spring", "spring boot",
    "dotnet", ".net", "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch",
    "keras", "nlp", "machine learning", "deep learning", "data analysis", "power bi",
    "tableau", "excel", "looker", "spark", "hadoop", "airflow", "aws", "azure", "gcp",
    "docker", "kubernetes", "jenkins", "git", "github", "gitlab", "ci/cd", "linux",
    "rest api", "graphql", "microservices", "terraform", "ansible", "selenium",
    "cypress", "jira", "figma", "adobe xd", "photoshop", "illustrator", "canva",
    "android", "ios", "react native", "flutter", "firebase", "salesforce", "sap",
    "servicenow", "snowflake", "bigquery", "dbt", "kafka", "elasticsearch",
    "prompt engineering", "llm", "openai", "langchain", "mlops", "devops",
    "html5", "css3", "bootstrap", "tailwind", "redux", "webpack", "vite",
]

BUSINESS_SKILLS = [
    "project management", "agile", "scrum", "kanban", "stakeholder management",
    "business analysis", "requirement gathering", "product management", "roadmap",
    "market research", "digital marketing", "seo", "sem", "google ads", "meta ads",
    "content marketing", "email marketing", "social media", "copywriting", "branding",
    "sales", "business development", "lead generation", "crm", "negotiation",
    "account management", "customer success", "customer support", "hr", "recruitment",
    "talent acquisition", "payroll", "onboarding", "performance management",
    "accounting", "bookkeeping", "tally", "gst", "taxation", "financial analysis",
    "budgeting", "forecasting", "audit", "compliance", "risk management",
    "operations", "supply chain", "procurement", "inventory", "logistics",
    "communication", "presentation", "leadership", "team management", "training",
    "ms office", "powerpoint", "word", "google analytics", "hubspot", "zoho",
    "public speaking", "problem solving", "critical thinking", "data visualization",
    "ux research", "wireframing", "prototyping", "user research", "a/b testing",
]

ALL_SKILLS = sorted(set(TECH_SKILLS + BUSINESS_SKILLS), key=len, reverse=True)

ACTION_VERBS = [
    "achieved", "administered", "analyzed", "architected", "automated", "built",
    "collaborated", "created", "delivered", "designed", "developed", "directed",
    "drove", "engineered", "established", "executed", "expanded", "improved",
    "increased", "implemented", "launched", "led", "managed", "mentored",
    "migrated", "optimized", "owned", "reduced", "redesigned", "refactored",
    "scaled", "shipped", "spearheaded", "streamlined", "transformed", "won",
]

WEAK_PHRASES = [
    "responsible for", "duties included", "hard working", "team player",
    "references available", "seeking a challenging", "dynamic environment",
    "guru", "ninja", "rockstar", "synergy", "go-getter", "detail-oriented",
]

ROLE_FAMILIES: list[RoleFamily] = [
    {
        "key": "software_engineer",
        "label": "Software Engineering",
        "titles": [
            "Software Engineer", "Software Developer", "Full Stack Developer",
            "Backend Developer", "Frontend Developer", "Python Developer",
            "Java Developer", "React Developer", "SDE", "SDE-1", "SDE-2",
        ],
        "keywords": [
            "python", "java", "javascript", "react", "node.js", "sql", "git",
            "rest api", "docker", "aws", "microservices", "django", "spring",
        ],
    },
    {
        "key": "data",
        "label": "Data & Analytics",
        "titles": [
            "Data Analyst", "Data Scientist", "Business Analyst", "BI Analyst",
            "Data Engineer", "ML Engineer", "Analytics Engineer",
        ],
        "keywords": [
            "sql", "python", "excel", "tableau", "power bi", "pandas",
            "machine learning", "statistics", "etl", "data analysis",
        ],
    },
    {
        "key": "devops",
        "label": "DevOps & Cloud",
        "titles": [
            "DevOps Engineer", "Cloud Engineer", "SRE", "Platform Engineer",
            "AWS Engineer", "Site Reliability Engineer",
        ],
        "keywords": [
            "aws", "azure", "docker", "kubernetes", "ci/cd", "terraform",
            "linux", "jenkins", "monitoring", "ansible",
        ],
    },
    {
        "key": "product",
        "label": "Product",
        "titles": [
            "Product Manager", "Associate Product Manager", "Product Owner",
            "Product Analyst",
        ],
        "keywords": [
            "product management", "roadmap", "agile", "stakeholder management",
            "user research", "a/b testing", "jira", "sql",
        ],
    },
    {
        "key": "design",
        "label": "Design",
        "titles": [
            "UI Designer", "UX Designer", "UI/UX Designer", "Product Designer",
            "Graphic Designer",
        ],
        "keywords": [
            "figma", "adobe xd", "wireframing", "prototyping", "user research",
            "photoshop", "illustrator", "ux research",
        ],
    },
    {
        "key": "marketing",
        "label": "Marketing",
        "titles": [
            "Digital Marketing Executive", "Marketing Manager", "SEO Specialist",
            "Content Writer", "Social Media Manager", "Performance Marketer",
        ],
        "keywords": [
            "digital marketing", "seo", "google ads", "meta ads", "analytics",
            "content marketing", "social media", "email marketing",
        ],
    },
    {
        "key": "sales",
        "label": "Sales & BD",
        "titles": [
            "Sales Executive", "Business Development Executive", "Account Manager",
            "Inside Sales", "BDE", "Sales Manager",
        ],
        "keywords": [
            "sales", "lead generation", "crm", "negotiation", "business development",
            "account management", "pipeline",
        ],
    },
    {
        "key": "hr",
        "label": "Human Resources",
        "titles": [
            "HR Executive", "Talent Acquisition Specialist", "Recruiter",
            "HR Generalist", "HR Manager",
        ],
        "keywords": [
            "recruitment", "talent acquisition", "onboarding", "payroll",
            "hr", "employee engagement",
        ],
    },
    {
        "key": "finance",
        "label": "Finance & Accounting",
        "titles": [
            "Accountant", "Financial Analyst", "Accounts Executive",
            "Audit Associate", "Finance Executive",
        ],
        "keywords": [
            "accounting", "tally", "gst", "excel", "financial analysis",
            "taxation", "audit", "budgeting",
        ],
    },
    {
        "key": "support",
        "label": "Customer & Operations",
        "titles": [
            "Customer Support Executive", "Operations Executive",
            "Customer Success Associate", "Process Associate",
        ],
        "keywords": [
            "customer support", "communication", "crm", "operations",
            "ticketing", "sla",
        ],
    },
]

TITLE_HINTS = [
    "software engineer", "software developer", "full stack", "frontend", "backend",
    "data analyst", "data scientist", "data engineer", "business analyst",
    "product manager", "project manager", "scrum master", "devops", "sre",
    "ui/ux", "ux designer", "ui designer", "graphic designer",
    "digital marketing", "seo", "content writer", "social media",
    "sales executive", "business development", "account manager",
    "hr executive", "recruiter", "talent acquisition",
    "accountant", "financial analyst", "chartered accountant",
    "customer support", "customer success", "operations",
    "java developer", "python developer", "react developer", "android developer",
    "machine learning", "ml engineer", "qa engineer", "test engineer",
    "system administrator", "network engineer", "cybersecurity",
]
