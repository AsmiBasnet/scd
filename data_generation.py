import sqlite3
import random
from datetime import datetime, timedelta
import math

DB_NAME = "scd_workforce.db"

# Sample lists for generating randomized names and departments
FIRST_NAMES = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", 
               "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
               "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
               "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
               "Steven", "Dorothy", "Paul", "Kimberly", "Andrew", "Emily", "Joshua", "Donna"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", 
              "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", 
              "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", 
              "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", 
              "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores"]

DEPARTMENTS = [
    ("Entertainment Business", "Academic"),
    ("Film & Television", "Academic"),
    ("Game Design & Development", "Academic"),
    ("Creative Writing", "Academic"),
    ("Music & Recording Arts", "Academic"),
    ("Administration & HR", "Operations"),
    ("Information Technology", "Operations"),
    ("Marketing & Admissions", "Operations"),
    ("Student Support Services", "Support"),
    ("Facilities & Security", "Operations")
]

SCD_PROGRAMS = [
    ("New Employee Orientation", "Onboarding"),
    ("Navigator School", "Professional Development"),
    ("Spring Learn & Grow", "Community"),
    ("Summer Learn & Grow", "Community"),
    ("Winter Leadership Summit", "Professional Development")
]

# Theme templates for comment simulation
THEME_TEMPLATES = {
    "onboarding clarity": {
        "positive": [
            "The New Employee Orientation was incredibly welcoming and clear.",
            "Great onboarding process! Everything was organized and I knew exactly what to do.",
            "Navigator School made my transition into my academic role seamless.",
            "Really appreciated the onboarding clarity and friendly introductions on day one."
        ],
        "neutral": [
            "The onboarding was fine, but there was a lot of information at once.",
            "New hire orientation was okay, standard corporate details.",
            "Onboarding materials were complete, though a bit overwhelming."
        ],
        "negative": [
            "I felt lost during my first week; the onboarding clarity was lacking.",
            "Orientation was rushed, and I still don't know who to contact for basic software access.",
            "The onboarding session was disorganized and did not help me understand my role."
        ]
    },
    "manager communication": {
        "positive": [
            "My department head communicates changes clearly and always listens to feedback.",
            "Manager communication has been excellent; we have weekly check-ins.",
            "I feel fully supported by my lead. They explain goals and changes very well.",
            "Excellent support from my manager during the recent academic restructuring."
        ],
        "neutral": [
            "Manager communication is standard, mostly emails and brief meetings.",
            "Communication is okay, but sometimes department updates are delayed.",
            "Our director communicates when necessary, though could be more proactive."
        ],
        "negative": [
            "Communication from leadership is poor; we only hear about decisions after they are made.",
            "My manager is rarely available, and check-ins are constantly rescheduled.",
            "Lack of manager communication makes it hard to coordinate department projects.",
            "Decisions are handed down without context or explanation."
        ]
    },
    "event schedules": {
        "positive": [
            "The Learn & Grow events are scheduled perfectly during our down times.",
            "Great timing on the SCD programs! Easy to attend and well run.",
            "Love the event schedules this year, very considerate of teaching hours.",
            "Having online and in-person options for workshops has made attendance much easier."
        ],
        "neutral": [
            "The event schedules are fine, but sometimes conflict with student office hours.",
            "SCD events are okay, calendar invites are sent out on time.",
            "Workshops are scheduled fine, though afternoon sessions can feel long."
        ],
        "negative": [
            "The SCD events are scheduled during lectures, making it impossible for faculty to attend.",
            "Event schedules are always conflicting with course prep and grading windows.",
            "SCD event invitations are sent last-minute, causing scheduling conflicts."
        ]
    },
    "compensation": {
        "positive": [
            "Compensation packages are competitive and benefits are great.",
            "Satisfied with my pay scale and performance incentives.",
            "The yearly merit reviews are fair and reward dedication."
        ],
        "neutral": [
            "Salary is average for the academic industry, benefits are standard.",
            "Compensation is ok, but cost-of-living adjustments are needed.",
            "Compensation is acceptable, but does not match regional changes."
        ],
        "negative": [
            "Compensation is below market rate for this level of academic responsibility.",
            "Salary growth is slow and does not keep up with inflation.",
            "Low pay scale compared to other universities in the state.",
            "Exited due to better compensation offers from competitors."
        ]
    },
    "workload": {
        "positive": [
            "Work-life balance is well maintained here. Workload is manageable.",
            "Appreciate the realistic course loading and prep schedules.",
            "My department does a great job balancing operational demands and teaching hours."
        ],
        "neutral": [
            "Workload is standard, busy during course launches but quiet later.",
            "The pace is fast, but we manage with team support.",
            "Expected amount of administrative tasks for a university role."
        ],
        "negative": [
            "The teaching load is too high, leaving no time for course development or grading.",
            "Constant administrative overhead has led to extreme burnout.",
            "Short-staffing has doubled our operational workload with no relief in sight."
        ]
    },
    "outliers": [
        "I lost my building badge yesterday near the parking lot.",
        "Does anyone know if the cafeteria is open on weekends?",
        "It would be nice to have a coffee machine on the third floor.",
        "The weather in Winter Park has been extremely humid this week.",
        "Could we get better whiteboard markers for the classrooms?",
        "Is there a test comment system here?",
        "The parking garage is always full by 9:00 AM.",
        "Need more printer paper in block 3."
    ]
}

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Drop existing tables to ensure clean run
    cursor.execute("DROP TABLE IF EXISTS Fact_Sentiment_Feedback")
    cursor.execute("DROP TABLE IF EXISTS Fact_Employee_Events")
    cursor.execute("DROP TABLE IF EXISTS Dim_Department")
    cursor.execute("DROP TABLE IF EXISTS Dim_SCD_Program")

    # Create tables
    cursor.execute("""
    CREATE TABLE Dim_Department (
        dept_id INTEGER PRIMARY KEY AUTOINCREMENT,
        dept_name TEXT NOT NULL UNIQUE,
        division TEXT NOT NULL
    )""")

    cursor.execute("""
    CREATE TABLE Dim_SCD_Program (
        program_id INTEGER PRIMARY KEY AUTOINCREMENT,
        program_name TEXT NOT NULL UNIQUE,
        program_type TEXT NOT NULL
    )""")

    cursor.execute("""
    CREATE TABLE Fact_Employee_Events (
        employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_name TEXT NOT NULL,
        dept_id INTEGER,
        hire_date TEXT NOT NULL,
        orientation_completed INTEGER DEFAULT 0,
        orientation_date TEXT,
        navigator_school_completed INTEGER DEFAULT 0,
        navigator_school_date TEXT,
        performance_rating INTEGER CHECK(performance_rating BETWEEN 1 AND 5),
        retention_status TEXT CHECK(retention_status IN ('Active', 'Exited')) NOT NULL,
        exit_date TEXT,
        FOREIGN KEY (dept_id) REFERENCES Dim_Department(dept_id)
    )""")

    cursor.execute("""
    CREATE TABLE Fact_Sentiment_Feedback (
        feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        survey_date TEXT NOT NULL,
        source TEXT CHECK(source IN ('Glassdoor', 'Internal Survey', 'Exit Interview')) NOT NULL,
        raw_text TEXT NOT NULL,
        sentiment_score REAL,
        sentiment_class TEXT,
        relevance_score REAL,
        theme TEXT,
        FOREIGN KEY (employee_id) REFERENCES Fact_Employee_Events(employee_id)
    )""")

    # Insert dimensions
    cursor.executemany("INSERT INTO Dim_Department (dept_name, division) VALUES (?, ?)", DEPARTMENTS)
    cursor.executemany("INSERT INTO Dim_SCD_Program (program_name, program_type) VALUES (?, ?)", SCD_PROGRAMS)

    conn.commit()
    conn.close()

def generate_data(num_employees=10000, num_comments=3000):
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Get departments
    cursor.execute("SELECT dept_id, dept_name FROM Dim_Department")
    depts = cursor.fetchall()
    
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2026, 8, 1)
    date_range_days = (end_date - start_date).days

    print(f"Generating {num_employees} employees...")

    employees = []
    
    # Track statistics for logging
    exited_count = 0
    orientation_count = 0
    navigator_count = 0

    for emp_id in range(1, num_employees + 1):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        name = f"{first} {last}"
        
        dept_id, dept_name = random.choice(depts)
        
        # Randomize hire date
        random_days = random.randint(0, date_range_days)
        hire_dt = start_date + timedelta(days=random_days)
        hire_date_str = hire_dt.strftime("%Y-%m-%d")

        # Program completions (correlated with department types or randomized)
        # Academic departments might have higher/lower participation
        orientation_rate = 0.90 if "Game" in dept_name or "Film" in dept_name else 0.82
        navigator_rate = 0.50 if "Entertainment" in dept_name or "Writing" in dept_name else 0.35

        orientation_completed = 1 if random.random() < orientation_rate else 0
        orientation_date_str = None
        if orientation_completed:
            orientation_dt = hire_dt + timedelta(days=random.randint(1, 14))
            orientation_date_str = orientation_dt.strftime("%Y-%m-%d")
            orientation_count += 1

        navigator_school_completed = 0
        navigator_school_date_str = None
        if orientation_completed and random.random() < navigator_rate:
            navigator_school_completed = 1
            navigator_dt = hire_dt + timedelta(days=random.randint(30, 180))
            navigator_school_date_str = navigator_dt.strftime("%Y-%m-%d")
            navigator_count += 1

        # Performance rating (1 to 5)
        # Slightly positive skew, higher performance for trained employees
        if orientation_completed and navigator_school_completed:
            perf_weights = [0.02, 0.05, 0.25, 0.45, 0.23] # Higher ratings
        elif orientation_completed:
            perf_weights = [0.03, 0.10, 0.35, 0.40, 0.12]
        else:
            perf_weights = [0.10, 0.20, 0.45, 0.20, 0.05] # Lower ratings
        performance_rating = random.choices([1, 2, 3, 4, 5], weights=perf_weights)[0]

        # Retention logic - CRITICAL correlation
        # Trained employees (Orientation + Navigator) have low exit rate (~4%)
        # Trained only in Orientation have medium exit rate (~12%)
        # Untrained have high exit rate (~32%)
        if orientation_completed and navigator_school_completed:
            exit_prob = 0.04
        elif orientation_completed:
            exit_prob = 0.12
        else:
            exit_prob = 0.32
            
        retention_status = "Active"
        exit_date_str = None
        if random.random() < exit_prob:
            retention_status = "Exited"
            # Exit occurs 30 to 600 days after hire
            exit_dt = hire_dt + timedelta(days=random.randint(30, 600))
            # Don't let exit date exceed our data ceiling
            if exit_dt < end_date:
                exit_date_str = exit_dt.strftime("%Y-%m-%d")
                exited_count += 1
            else:
                retention_status = "Active" # If exit date is in future, they are still active

        employees.append((
            name, dept_id, hire_date_str, 
            orientation_completed, orientation_date_str,
            navigator_school_completed, navigator_school_date_str,
            performance_rating, retention_status, exit_date_str
        ))

    cursor.executemany("""
        INSERT INTO Fact_Employee_Events (
            employee_name, dept_id, hire_date, 
            orientation_completed, orientation_date,
            navigator_school_completed, navigator_school_date,
            performance_rating, retention_status, exit_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, employees)
    
    conn.commit()

    # Generate comments
    print(f"Generating {num_comments} feedback comments...")
    
    # Get active/exited employees to link comments
    cursor.execute("SELECT employee_id, retention_status, hire_date, exit_date FROM Fact_Employee_Events")
    all_employees = cursor.fetchall()
    
    comments = []
    
    for i in range(num_comments):
        # Pick random employee or anonymous
        emp = random.choice(all_employees)
        emp_id, status, hire_date_str, exit_date_str = emp
        hire_dt = datetime.strptime(hire_date_str, "%Y-%m-%d")
        
        # Determine source
        if status == "Exited" and random.random() < 0.4:
            source = "Exit Interview"
            # Date near the exit
            exit_dt = datetime.strptime(exit_date_str, "%Y-%m-%d")
            survey_dt = exit_dt - timedelta(days=random.randint(0, 15))
        else:
            source = random.choices(["Internal Survey", "Glassdoor"], weights=[0.75, 0.25])[0]
            if status == "Exited":
                exit_dt = datetime.strptime(exit_date_str, "%Y-%m-%d")
                days_active = (exit_dt - hire_dt).days
                survey_dt = hire_dt + timedelta(days=random.randint(0, max(1, days_active)))
            else:
                days_active = (end_date - hire_dt).days
                survey_dt = hire_dt + timedelta(days=random.randint(0, max(1, days_active)))

        survey_date_str = survey_dt.strftime("%Y-%m-%d")
        
        # Decide if comment is relevant or an outlier
        is_outlier = random.random() < 0.12 # 12% outlier/noise rate
        
        if is_outlier:
            raw_text = random.choice(THEME_TEMPLATES["outliers"])
        else:
            # Pick a regular theme and a sentiment
            theme = random.choice(list(THEME_TEMPLATES.keys() - ["outliers"]))
            
            # If Exit Interview, skew more negative. Glassdoor is mixed. Internal is positive/neutral.
            if source == "Exit Interview":
                sentiment = random.choices(["negative", "neutral", "positive"], weights=[0.75, 0.20, 0.05])[0]
            elif source == "Glassdoor":
                sentiment = random.choices(["negative", "neutral", "positive"], weights=[0.30, 0.30, 0.40])[0]
            else: # Internal Survey
                sentiment = random.choices(["positive", "neutral", "negative"], weights=[0.55, 0.30, 0.15])[0]
                
            raw_text = random.choice(THEME_TEMPLATES[theme][sentiment])

        comments.append((
            emp_id if source != "Glassdoor" else None, # Glassdoor is anonymous
            survey_date_str,
            source,
            raw_text
        ))

    cursor.executemany("""
        INSERT INTO Fact_Sentiment_Feedback (
            employee_id, survey_date, source, raw_text
        ) VALUES (?, ?, ?, ?)
    """, comments)

    conn.commit()
    conn.close()

    print(f"Data generation complete.")
    print(f"Summary statistics:")
    print(f"  - Total Employees: {num_employees}")
    print(f"  - Exited Employees: {exited_count} ({exited_count/num_employees*100:.1f}%)")
    print(f"  - Orientation Attendees: {orientation_count} ({orientation_count/num_employees*100:.1f}%)")
    print(f"  - Navigator School Attendees: {navigator_count} ({navigator_count/num_employees*100:.1f}%)")
    print(f"  - Total Feedback Comments: {num_comments}")

if __name__ == "__main__":
    generate_data()
