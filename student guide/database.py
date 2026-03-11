import sqlite3
import json

def init_db():
    conn = sqlite3.connect('career.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            education TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            description TEXT,
            required_skills TEXT,
            roadmap TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            category TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role_name TEXT,
            readiness_score INTEGER,
            matched_skills TEXT,
            missing_skills TEXT,
            roadmap TEXT,
            feedback TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Data
    skills_data = [
        ("Python", "Programming Languages"),
        ("Java", "Programming Languages"),
        ("C++", "Programming Languages"),
        ("JavaScript", "Programming Languages"),
        ("R Language", "Programming Languages"),
        ("C#", "Programming Languages"),
        ("Go", "Programming Languages"),
        ("Ruby", "Programming Languages"),
        ("Swift", "Programming Languages"),
        ("Kotlin", "Programming Languages"),

        ("HTML", "Web Development"),
        ("CSS", "Web Development"),
        ("React", "Web Development"),
        ("Node.js", "Web Development"),
        ("Angular", "Web Development"),
        ("Vue.js", "Web Development"),
        ("Django", "Web Development"),
        ("Flask", "Web Development"),
        
        ("Operating Systems", "Core Computer Science"),
        ("DBMS", "Core Computer Science"),
        ("Computer Networks", "Core Computer Science"),
        ("Data Structures and Algorithms", "Core Computer Science"),
        ("Software Engineering", "Core Computer Science"),
        
        ("Machine Learning", "Advanced Technologies"),
        ("Deep Learning", "Advanced Technologies"),
        ("Artificial Intelligence", "Advanced Technologies"),
        ("Data Analysis", "Advanced Technologies"),
        ("Statistics", "Advanced Technologies"),

        ("TensorFlow", "AI Tools & Frameworks"),
        ("PyTorch", "AI Tools & Frameworks"),
        ("Scikit-learn", "AI Tools & Frameworks"),
        ("Git", "AI Tools & Frameworks"),
        ("Docker", "AI Tools & Frameworks"),
        ("Kubernetes", "AI Tools & Frameworks"),
        
        ("SQL", "Database"),
        ("NoSQL", "Database"),
        ("MongoDB", "Database"),
        ("PostgreSQL", "Database"),

        ("Cybersecurity Fundamentals", "Security"),
        ("Network Security", "Security"),
        ("Cryptography", "Security"),
        ("Ethical Hacking", "Security"),
        
        ("AWS", "Cloud Computing"),
        ("Azure", "Cloud Computing"),
        ("Google Cloud", "Cloud Computing"),
        ("Linux", "Cloud Computing")
    ]

    for skill, cat in skills_data:
        cursor.execute("INSERT OR IGNORE INTO skills (name, category) VALUES (?, ?)", (skill, cat))

    roles_data = [
        {
            "name": "Software Developer",
            "description": "Designs, develops, and tests software applications.",
            "required_skills": ["Java", "C++", "Python", "Data Structures and Algorithms", "Software Engineering", "DBMS", "Git"],
            "roadmap": [
                {"stage": 1, "title": "Programming Core", "desc": "Master Java, C++ or Python.", "skills_covered": ["Java", "C++", "Python"]},
                {"stage": 2, "title": "CS Fundamentals", "desc": "Study DSA and Database systems.", "skills_covered": ["Data Structures and Algorithms", "DBMS"]},
                {"stage": 3, "title": "Software Engineering", "desc": "Learn SDLC and version control.", "skills_covered": ["Software Engineering", "Git"]},
                {"stage": 4, "title": "Projects", "desc": "Build 2-3 end-to-end software applications.", "skills_covered": []}
            ]
        },
        {
            "name": "Web Developer",
            "description": "Builds and maintains websites and web applications.",
            "required_skills": ["HTML", "CSS", "JavaScript", "React", "Node.js", "Git"],
            "roadmap": [
                {"stage": 1, "title": "Frontend Basics", "desc": "Master layout and styling with HTML, CSS, and basic JS.", "skills_covered": ["HTML", "CSS", "JavaScript"]},
                {"stage": 2, "title": "Frontend Frameworks", "desc": "Learn a framework like React.", "skills_covered": ["React"]},
                {"stage": 3, "title": "Backend Basics", "desc": "Learn Node.js and basic databases.", "skills_covered": ["Node.js"]},
                {"stage": 4, "title": "Tools & Projects", "desc": "Use Git and build full stack apps.", "skills_covered": ["Git"]}
            ]
        },
        {
            "name": "Full Stack Developer",
            "description": "Handles both frontend and backend development.",
            "required_skills": ["HTML", "CSS", "JavaScript", "React", "Node.js", "SQL", "MongoDB", "DBMS", "Git"],
            "roadmap": [
                {"stage": 1, "title": "Frontend Development", "desc": "Build interactive UIs using HTML, CSS, JS, and React.", "skills_covered": ["HTML", "CSS", "JavaScript", "React"]},
                {"stage": 2, "title": "Backend & DB", "desc": "Create APIs and manage databases.", "skills_covered": ["Node.js", "SQL", "MongoDB", "DBMS"]},
                {"stage": 3, "title": "Deployment & Tools", "desc": "Master version control and hosting.", "skills_covered": ["Git"]},
                {"stage": 4, "title": "Projects", "desc": "Build comprehensive full stack web platforms.", "skills_covered": []}
            ]
        },
        {
            "name": "Data Scientist",
            "description": "Analyzes large amounts of complex raw and processed data to find patterns.",
            "required_skills": ["Python", "R Language", "Machine Learning", "Data Analysis", "Statistics", "SQL", "Scikit-learn"],
            "roadmap": [
                {"stage": 1, "title": "Data Manipulation", "desc": "Learn Python, R, and data analysis basics.", "skills_covered": ["Python", "R Language", "Data Analysis"]},
                {"stage": 2, "title": "Math & Stats", "desc": "Learn statistics required for modeling.", "skills_covered": ["Statistics"]},
                {"stage": 3, "title": "Database Querying", "desc": "Learn SQL and how to fetch data from DBMS.", "skills_covered": ["SQL"]},
                {"stage": 4, "title": "Machine Learning", "desc": "Train and evaluate models using scikit-learn.", "skills_covered": ["Machine Learning", "Scikit-learn"]},
                {"stage": 5, "title": "Portfolios", "desc": "Analyze real-world datasets and publish findings.", "skills_covered": []}
            ]
        },
        {
            "name": "Machine Learning Engineer",
            "description": "Designs and builds machine learning systems and models.",
            "required_skills": ["Python", "Machine Learning", "Data Structures and Algorithms", "SQL", "Scikit-learn", "TensorFlow", "Docker"],
            "roadmap": [
                {"stage": 1, "title": "Programming & Fundamentals", "desc": "Master Python and DSA.", "skills_covered": ["Python", "Data Structures and Algorithms"]},
                {"stage": 2, "title": "Core ML & Data", "desc": "Learn scikit-learn and SQL.", "skills_covered": ["Machine Learning", "SQL", "Scikit-learn"]},
                {"stage": 3, "title": "Advanced ML & Tools", "desc": "Learn TensorFlow and deep learning basics.", "skills_covered": ["TensorFlow"]},
                {"stage": 4, "title": "Deployment", "desc": "Learn Docker for model deployment.", "skills_covered": ["Docker"]},
                {"stage": 5, "title": "Projects", "desc": "Build and deploy 3-4 ML models.", "skills_covered": []}
            ]
        },
        {
            "name": "Artificial Intelligence Engineer",
            "description": "Focuses on developing AI models, neural networks, and intelligent system architectures.",
            "required_skills": ["Python", "Artificial Intelligence", "Deep Learning", "Machine Learning", "TensorFlow", "PyTorch", "Data Structures and Algorithms"],
            "roadmap": [
                {"stage": 1, "title": "Theory & Core", "desc": "Understand AI, ML, and deep learning math.", "skills_covered": ["Artificial Intelligence", "Machine Learning", "Deep Learning"]},
                {"stage": 2, "title": "Programming", "desc": "Master Python and algorithms.", "skills_covered": ["Python", "Data Structures and Algorithms"]},
                {"stage": 3, "title": "Frameworks", "desc": "Hands-on with TensorFlow or PyTorch.", "skills_covered": ["TensorFlow", "PyTorch"]},
                {"stage": 4, "title": "Projects", "desc": "Build AI agents, NLP models, or computer vision applications.", "skills_covered": []}
            ]
        },
        {
            "name": "Cybersecurity Analyst",
            "description": "Protects systems and networks from cyber threats.",
            "required_skills": ["Python", "Computer Networks", "Operating Systems", "Cybersecurity Fundamentals", "Network Security", "Cryptography", "Linux"],
            "roadmap": [
                {"stage": 1, "title": "Networking & OS", "desc": "Master how computers communicate and operate.", "skills_covered": ["Computer Networks", "Operating Systems", "Linux"]},
                {"stage": 2, "title": "Security Basics", "desc": "Learn fundamental cybersecurity principles.", "skills_covered": ["Cybersecurity Fundamentals"]},
                {"stage": 3, "title": "Advanced Security", "desc": "Network security monitoring and cryptography.", "skills_covered": ["Network Security", "Cryptography"]},
                {"stage": 4, "title": "Practical Testing", "desc": "Practice penetration testing.", "skills_covered": []}
            ]
        },
        {
            "name": "Cloud Engineer",
            "description": "Designs, implements, and manages cloud-based systems and processes.",
            "required_skills": ["Linux", "Computer Networks", "AWS", "Azure", "Google Cloud", "Docker", "Python", "SQL"],
            "roadmap": [
                {"stage": 1, "title": "OS & Networking", "desc": "Master Linux and networking fundamentals.", "skills_covered": ["Linux", "Computer Networks"]},
                {"stage": 2, "title": "Programming & DB", "desc": "Learn basic scripting and databases.", "skills_covered": ["Python", "SQL"]},
                {"stage": 3, "title": "Cloud Platforms", "desc": "Gain expertise in AWS, Azure, or GCP.", "skills_covered": ["AWS", "Azure", "Google Cloud"]},
                {"stage": 4, "title": "Containerization", "desc": "Learn Docker basics.", "skills_covered": ["Docker"]}
            ]
        },
        {
            "name": "DevOps Engineer",
            "description": "Bridges development and operations by automating deployment and management.",
            "required_skills": ["Linux", "Git", "Docker", "Kubernetes", "AWS", "Python", "Computer Networks"],
            "roadmap": [
                {"stage": 1, "title": "System Admin", "desc": "Master Linux, networking, and scripting.", "skills_covered": ["Linux", "Python", "Computer Networks"]},
                {"stage": 2, "title": "CI/CD & Version Control", "desc": "Learn Git and CI/CD pipelines.", "skills_covered": ["Git"]},
                {"stage": 3, "title": "Containers & Orchestration", "desc": "Master Docker and Kubernetes.", "skills_covered": ["Docker", "Kubernetes"]},
                {"stage": 4, "title": "Cloud & Infrastructure", "desc": "Manage cloud resources using AWS.", "skills_covered": ["AWS"]}
            ]
        },
        {
            "name": "Mobile Application Developer",
            "description": "Creates applications for mobile devices such as smartphones and tablets.",
            "required_skills": ["Java", "Kotlin", "Swift", "React", "Data Structures and Algorithms", "SQL", "Git"],
            "roadmap": [
                {"stage": 1, "title": "Programming Core", "desc": "Learn Java, Kotlin, Swift, or React Native.", "skills_covered": ["Java", "Kotlin", "Swift", "React"]},
                {"stage": 2, "title": "Fundamentals", "desc": "Master algorithms and version control.", "skills_covered": ["Data Structures and Algorithms", "Git"]},
                {"stage": 3, "title": "Local Storage", "desc": "Understand mobile databases like SQLite.", "skills_covered": ["SQL"]},
                {"stage": 4, "title": "Projects", "desc": "Build and publish 2 mobile apps.", "skills_covered": []}
            ]
        }
    ]

    for role in roles_data:
        cursor.execute("INSERT OR REPLACE INTO roles (name, description, required_skills, roadmap) VALUES (?, ?, ?, ?)",
                       (role['name'], role['description'], json.dumps(role['required_skills']), json.dumps(role['roadmap'])))

    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == '__main__':
    init_db()
