import sqlite3
import time
import random
import datetime
from faker import Faker

fake = Faker()
DB_FILE = 'academic_data.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Create tables if they don't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            grade_level INTEGER,
            enrollment_date TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            date TEXT,
            status TEXT,
            FOREIGN KEY(student_id) REFERENCES students(student_id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS performance (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject TEXT,
            score REAL,
            exam_date TEXT,
            FOREIGN KEY(student_id) REFERENCES students(student_id)
        )
    ''')
    
    conn.commit()
    return conn

def seed_initial_data(conn, num_students=100):
    c = conn.cursor()
    c.execute('SELECT count(*) FROM students')
    if c.fetchone()[0] > 0:
        return # Data already seeded
    
    print(f"Seeding initial {num_students} students...")
    subjects = ['Math', 'Science', 'English', 'History', 'Art']
    
    for _ in range(num_students):
        first_name = fake.first_name()
        last_name = fake.last_name()
        grade_level = random.randint(9, 12)
        # Random enrollment date in the past year
        enrollment_date = fake.date_between(start_date='-1y', end_date='today').isoformat()
        
        c.execute('INSERT INTO students (first_name, last_name, grade_level, enrollment_date) VALUES (?, ?, ?, ?)',
                  (first_name, last_name, grade_level, enrollment_date))
        student_id = c.lastrowid
        
        # Seed some historical performance
        for _ in range(random.randint(2, 5)):
            subj = random.choice(subjects)
            # Create some occasional anomalies for the validation section
            if random.random() < 0.05:
                score = random.uniform(-20, 0) # Negative score (anomaly)
            elif random.random() < 0.05:
                score = random.uniform(101, 150) # Score > 100 (anomaly)
            else:
                score = random.uniform(50, 100) # Normal score
                score = round(score, 2)
                
            exam_date = fake.date_between(start_date='-6m', end_date='today').isoformat()
            c.execute('INSERT INTO performance (student_id, subject, score, exam_date) VALUES (?, ?, ?, ?)',
                      (student_id, subj, score, exam_date))
    
    conn.commit()
    print("Initial seeding complete.")

def simulate_realtime_data():
    conn = init_db()
    seed_initial_data(conn)
    c = conn.cursor()
    
    subjects = ['Math', 'Science', 'English', 'History', 'Art']
    statuses = ['Present', 'Absent', 'Late', 'Excused']
    
    print("Starting real-time data simulation... (Press Ctrl+C to stop)")
    try:
        while True:
            # Get list of existing students
            c.execute('SELECT student_id FROM students')
            student_ids = [row[0] for row in c.fetchall()]
            
            if not student_ids:
                time.sleep(1)
                continue

            event_type = random.choice(['attendance', 'performance', 'new_enrollment'])
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            
            if event_type == 'attendance':
                # Generate a batch of attendance records
                num_records = random.randint(1, 10)
                for _ in range(num_records):
                    s_id = random.choice(student_ids)
                    status = random.choices(statuses, weights=[0.8, 0.1, 0.05, 0.05])[0]
                    # Sometimes generate attendance without a valid student_id (anomaly)
                    if random.random() < 0.02:
                        s_id = max(student_ids) + 1000 
                    
                    c.execute('INSERT INTO attendance (student_id, date, status) VALUES (?, ?, ?)',
                              (s_id, today, status))
                print(f"Generated {num_records} attendance logs.")

            elif event_type == 'performance':
                s_id = random.choice(student_ids)
                subj = random.choice(subjects)
                
                if random.random() < 0.05:
                    score = random.uniform(-10, -1) # anomaly
                else:
                    score = round(random.uniform(50, 100), 2)
                    
                c.execute('INSERT INTO performance (student_id, subject, score, exam_date) VALUES (?, ?, ?, ?)',
                          (s_id, subj, score, today))
                print(f"Generated performance record for Student {s_id}: {subj} - {score}")
            
            elif event_type == 'new_enrollment':
                # 10% chance to actually enroll someone so it doesn't grow too fast
                if random.random() < 0.1:
                    first_name = fake.first_name()
                    last_name = fake.last_name()
                    grade_level = random.randint(9, 12)
                    enroll_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    c.execute('INSERT INTO students (first_name, last_name, grade_level, enrollment_date) VALUES (?, ?, ?, ?)',
                              (first_name, last_name, grade_level, enroll_date))
                    print(f"New student enrolled: {first_name} {last_name} (Grade {grade_level})")

            conn.commit()
            
            # Sleep a random amount of time between 2 to 5 seconds
            time.sleep(random.uniform(2, 5))
            
    except KeyboardInterrupt:
        print("\nSimulation stopped.")
    finally:
        conn.close()

if __name__ == '__main__':
    simulate_realtime_data()
