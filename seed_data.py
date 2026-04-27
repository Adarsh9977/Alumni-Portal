# seed_data.py - Populate database with dummy data for testing

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, engine, Base
from app.models import User, Job, Event, Post, Comment, Like, Application, Connection, EventParticipant, Message
from app.auth import get_password_hash

# Create tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Clear existing data
print("Clearing existing data...")
db.query(Message).delete()
db.query(EventParticipant).delete()
db.query(Connection).delete()
db.query(Like).delete()
db.query(Comment).delete()
db.query(Application).delete()
db.query(Post).delete()
db.query(Job).delete()
db.query(Event).delete()
db.query(User).delete()
db.commit()

# ===== USERS =====
print("👤 Creating users...")
password = get_password_hash("password123")

admin = User(name="Rahul Sharma", email="admin@alumni.com", hashed_password=password, role="admin",
    batch="2018", branch="Computer Science", company="Alumni Nexus", skills="Management, Python, Leadership", bio="Platform administrator and CS graduate.", profile_picture="https://i.pravatar.cc/150?u=admin")

alumni1 = User(name="Priya Patel", email="priya@alumni.com", hashed_password=password, role="alumni",
    batch="2019", branch="Computer Science", company="Google India", skills="Python, Machine Learning, Cloud", bio="Senior ML Engineer at Google. Passionate about AI and mentoring students.", profile_picture="https://i.pravatar.cc/150?u=priya")

alumni2 = User(name="Amit Kumar", email="amit@alumni.com", hashed_password=password, role="alumni",
    batch="2018", branch="Electronics", company="Microsoft", skills="Azure, C#, .NET, DevOps", bio="Cloud Architect at Microsoft. Building scalable enterprise solutions.", profile_picture="https://i.pravatar.cc/150?u=amit")

alumni3 = User(name="Sneha Reddy", email="sneha@alumni.com", hashed_password=password, role="alumni",
    batch="2020", branch="Information Technology", company="Amazon", skills="Java, AWS, System Design", bio="SDE-2 at Amazon. Open source contributor and tech speaker.",
    ats_score=85, ats_feedback="Excellent resume with strong focus on Java/AWS.", profile_picture="https://i.pravatar.cc/150?u=sneha")

alumni4 = User(name="Vikram Singh", email="vikram@alumni.com", hashed_password=password, role="alumni",
    batch="2017", branch="Mechanical", company="Tata Motors", skills="AutoCAD, MATLAB, Product Design", bio="Lead Product Engineer at Tata Motors. Innovating in EV technology.", profile_picture="https://i.pravatar.cc/150?u=vikram")

alumni5 = User(name="Neha Gupta", email="neha@alumni.com", hashed_password=password, role="alumni",
    batch="2021", branch="Computer Science", company="Flipkart", skills="React, Node.js, TypeScript, MongoDB", bio="Full Stack Developer at Flipkart. Building the future of e-commerce.", profile_picture="https://i.pravatar.cc/150?u=neha")

# 10 More Alumni as requested (name@gmail.com)
more_alumni = [
    User(name="Anil Kapur", email="anil@gmail.com", hashed_password=password, role="alumni", batch="2015", branch="Mechanical", company="Tesla", skills="Robotics", bio="Engineering lead."),
    User(name="Bina Dash", email="bina@gmail.com", hashed_password=password, role="alumni", batch="2016", branch="IT", company="Meta", skills="Frontend", bio="Senior Developer."),
    User(name="Chetan Jain", email="chetan@gmail.com", hashed_password=password, role="alumni", batch="2014", branch="CS", company="Netflix", skills="Backend", bio="Architect."),
    User(name="Deepa Mani", email="deepa@gmail.com", hashed_password=password, role="alumni", batch="2017", branch="Electronics", company="Intel", skills="Hardware", bio="Design Engineer."),
    User(name="Esha Rao", email="esha@gmail.com", hashed_password=password, role="alumni", batch="2018", branch="Civil", company="L&T", skills="Structures", bio="Project Manager."),
    User(name="Farhan Ali", email="farhan@gmail.com", hashed_password=password, role="alumni", batch="2013", branch="CS", company="IBM", skills="Mainframe", bio="Consultant."),
    User(name="Geeta Iyer", email="geeta@gmail.com", hashed_password=password, role="alumni", batch="2019", branch="IT", company="Adobe", skills="UI/UX", bio="Creative Lead."),
    User(name="Himesh Resh", email="himesh@gmail.com", hashed_password=password, role="alumni", batch="2012", branch="Electronics", company="Samsung", skills="Embedded", bio="Tech Lead."),
    User(name="Ishita Sen", email="ishita@gmail.com", hashed_password=password, role="alumni", batch="2020", branch="CS", company="Uber", skills="Distributed Systems", bio="SDE."),
    User(name="Jatin Lal", email="jatin@gmail.com", hashed_password=password, role="alumni", batch="2011", branch="Mechanical", company="Ford", skills="Automotive", bio="Director.")
]

student1 = User(name="Arjun Verma", email="student@alumni.com", hashed_password=password, role="student",
    batch="2025", branch="Computer Science", skills="Python, JavaScript, React", bio="Final year CS student. Looking for software engineering roles.", profile_picture="https://i.pravatar.cc/150?u=arjun")

student2 = User(name="Kavya Nair", email="kavya@alumni.com", hashed_password=password, role="student",
    batch="2025", branch="Electronics", skills="Embedded C, IoT, VLSI", bio="ECE student passionate about IoT and embedded systems.", profile_picture="https://i.pravatar.cc/150?u=kavya")

student3 = User(name="Rohan Mehta", email="rohan@alumni.com", hashed_password=password, role="student",
    batch="2026", branch="Information Technology", skills="Java, Spring Boot, MySQL", bio="Pre-final year IT student interested in backend development.", profile_picture="https://i.pravatar.cc/150?u=rohan")

# 10 More Students as requested (name@gmail.com)
more_students = [
    User(name="Karan Johar", email="karan@gmail.com", hashed_password=password, role="student", batch="2025", branch="CS", bio="Aspiring dev."),
    User(name="Laxmi Kant", email="laxmi@gmail.com", hashed_password=password, role="student", batch="2026", branch="IT", bio="Tech enthusiast."),
    User(name="Manoj Baj", email="manoj@gmail.com", hashed_password=password, role="student", batch="2027", branch="Electronics", bio="Learner."),
    User(name="Nitin Gad", email="nitin@gmail.com", hashed_password=password, role="student", batch="2025", branch="Mechanical", bio="Future engineer."),
    User(name="Om Puri", email="om@gmail.com", hashed_password=password, role="student", batch="2026", branch="Civil", bio="Hard worker."),
    User(name="Pankaj Trip", email="pankaj@gmail.com", hashed_password=password, role="student", batch="2027", branch="CS", bio="Coding is life."),
    User(name="Qasim Ali", email="qasim@gmail.com", hashed_password=password, role="student", batch="2025", branch="IT", bio="Security focused."),
    User(name="Rahul Roy", email="rahul@gmail.com", hashed_password=password, role="student", batch="2026", branch="Electronics", bio="Hardware fan."),
    User(name="Suniel Shet", email="suniel@gmail.com", hashed_password=password, role="student", batch="2027", branch="Mechanical", bio="Design lover."),
    User(name="Tina Munim", email="tina@gmail.com", hashed_password=password, role="student", batch="2025", branch="CS", bio="Fullstack path.")
]

users = [admin, alumni1, alumni2, alumni3, alumni4, alumni5, student1, student2, student3] + more_alumni + more_students
db.add_all(users)
db.commit()
for u in users:
    db.refresh(u)

# ===== CONNECTIONS =====
print("🤝 Creating connections...")
connections = []
seen_pairs = set()
for idx, sender in enumerate(users):
    for offset in (1, 2, 3):
        receiver = users[(idx + offset) % len(users)]
        pair = tuple(sorted((sender.id, receiver.id)))
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        connections.append(Connection(sender_id=sender.id, receiver_id=receiver.id, status="accepted"))

db.add_all(connections)
db.commit()

# ===== JOBS =====
print("💼 Creating jobs...")
jobs = [
    Job(title="Software Engineer - Python", description="We are looking for a Python developer to join our backend team. You'll work on building scalable APIs, microservices, and data pipelines. Experience with FastAPI or Django is a plus.", company="Google India", location="Bangalore", job_type="Full-time", salary_range="₹18-25 LPA", requirements="3+ years Python, REST APIs, SQL, Git", posted_by=alumni1.id, experience_level="Mid Level", category="IT / Software"),

    Job(title="Frontend Developer - React", description="Join our product team to build beautiful, performant user interfaces. You'll collaborate with designers and backend engineers to deliver amazing user experiences on Flipkart's platform.", company="Flipkart", location="Bangalore", job_type="Full-time", salary_range="₹15-22 LPA", requirements="React, TypeScript, CSS, 2+ years experience", posted_by=alumni5.id, experience_level="Mid Level", category="IT / Software"),

    Job(title="Cloud Engineer Intern", description="Summer internship opportunity in our Azure cloud team. You'll learn about cloud infrastructure, CI/CD pipelines, and work on real projects that impact millions of users worldwide.", company="Microsoft", location="Hyderabad", job_type="Internship", salary_range="₹50K/month stipend", requirements="Basic cloud knowledge, Linux, Programming fundamentals", posted_by=alumni2.id, experience_level="Entry Level", category="IT / Software"),

    Job(title="Data Scientist", description="Looking for a data scientist to work on recommendation systems and search ranking. You'll use ML models to improve customer experience across Amazon India's marketplace.", company="Amazon", location="Hyderabad (Hybrid)", job_type="Full-time", salary_range="₹20-30 LPA", requirements="ML/DL, Python, Statistics, 2+ years experience", posted_by=alumni3.id, experience_level="Mid Level", category="IT / Software"),

    Job(title="Backend Developer - Java", description="Build robust microservices for our e-commerce platform. Work with a talented team on high-scale distributed systems processing millions of requests daily.", company="Flipkart", location="Bangalore", job_type="Full-time", salary_range="₹16-24 LPA", requirements="Java, Spring Boot, Microservices, Kafka", posted_by=alumni5.id, experience_level="Mid Level", category="IT / Software"),

    Job(title="Product Design Engineer", description="Join our EV division to design next-generation electric vehicle components. Work with cutting-edge tools and collaborate with global engineering teams.", company="Tata Motors", location="Pune", job_type="Full-time", salary_range="₹12-18 LPA", requirements="AutoCAD, SolidWorks, Mechanical Engineering degree", posted_by=alumni4.id, experience_level="Mid Level", category="Core Engineering"),
]
db.add_all(jobs)
db.commit()
for j in jobs:
    db.refresh(j)

# ===== EVENTS =====
print("📅 Creating events...")
events = [
    Event(title="Alumni Meetup 2026 - Bangalore Chapter", description="Annual alumni meetup in Bangalore! Join fellow graduates for networking, talks by industry leaders, and a gala dinner. This is a great opportunity to reconnect and build new connections.", date="2026-04-15", time="18:00", location="Taj MG Road, Bangalore", event_type="Meetup", organized_by=admin.id),

    Event(title="AI & Machine Learning Workshop", description="Hands-on workshop on building ML pipelines using Python, TensorFlow, and cloud services. Learn from industry experts and get career guidance in the AI field.", date="2026-04-22", time="10:00", location="Online - Google Meet", event_type="Workshop", organized_by=alumni1.id),

    Event(title="Cloud Computing Masterclass", description="Deep dive into AWS, Azure, and GCP. Learn about serverless architecture, containers, and DevOps practices used at top tech companies.", date="2026-05-05", time="14:00", location="Online - Microsoft Teams", event_type="Webinar", organized_by=alumni2.id),

    Event(title="Campus Recruitment Prep Session", description="Tips and strategies for cracking campus placements. Mock interviews, resume reviews, and guidance from alumni who've been through the process.", date="2026-05-10", time="11:00", location="College Auditorium", event_type="Seminar", organized_by=admin.id),

    Event(title="Startup Stories - From Campus to Company", description="Hear inspiring stories from alumni entrepreneurs who started their companies after graduation. Q&A session and networking opportunities included.", date="2026-05-20", time="16:00", location="Innovation Hub, Campus", event_type="Conference", organized_by=alumni3.id),
]
db.add_all(events)
db.commit()

# ===== POSTS =====
print("📝 Creating posts...")
posts = [
    Post(title="Excited to join Google!", content="Thrilled to announce that I've joined Google India as a Senior ML Engineer!  The journey from our college to here has been incredible. Remember, every small step counts. Keep learning, keep growing! #NewBeginnings #GoogleIndia", author_id=alumni1.id),

    Post(title="Hiring for my team!", content="My team at Microsoft is hiring Cloud Engineers! If you're passionate about Azure and distributed systems, reach out to me. I'd love to refer fellow alumni. Check the jobs section for details. 🚀", author_id=alumni2.id),

    Post(content="Just completed my AWS Solutions Architect certification!  Highly recommend it for anyone interested in cloud computing. Happy to share study resources with juniors. DM me!", author_id=alumni3.id),

    Post(title="College memories ❤️", content="Visited our alma mater today after 5 years. So many memories! The new building looks amazing. Met some current students and their energy reminded me of our days. Time flies! 📸", author_id=alumni4.id),

    Post(content="Looking for internship opportunities in software development. I know Python, JavaScript, and React. Currently in my final year. Any leads would be appreciated! 🙏 #OpenToWork", author_id=student1.id),

    Post(title="Tips for coding interviews", content="After cracking interviews at 3 top tech companies, here are my tips:\n1. Master DSA fundamentals\n2. Practice on LeetCode daily\n3. Build real projects\n4. Mock interviews are key\n5. Stay consistent!\nGood luck to all the students preparing! 💪", author_id=alumni5.id),

    Post(content="Our college's placement season is going strong! 85% placement rate so far. Proud of our juniors! Alumni network truly makes a difference. 🎓", author_id=admin.id),
]
db.add_all(posts)
db.commit()
for p in posts:
    db.refresh(p)

# ===== COMMENTS =====
print("💬 Creating comments...")
comments = [
    Comment(content="Congratulations Priya! So proud of you! 🎉", post_id=posts[0].id, author_id=alumni2.id),
    Comment(content="Amazing achievement! You're an inspiration to all of us.", post_id=posts[0].id, author_id=student1.id),
    Comment(content="Well deserved! Google is lucky to have you.", post_id=posts[0].id, author_id=admin.id),

    Comment(content="Just applied! Thanks for sharing, Amit! 🙌", post_id=posts[1].id, author_id=student1.id),
    Comment(content="I'll share this with my batch mates!", post_id=posts[1].id, author_id=student2.id),

    Comment(content="Congrats Sneha! Can you share the study plan?", post_id=posts[2].id, author_id=student3.id),
    Comment(content="That's awesome! AWS certs are really valuable.", post_id=posts[2].id, author_id=alumni5.id),

    Comment(content="Those were the best days! Miss college life.", post_id=posts[3].id, author_id=alumni1.id),

    Comment(content="Arjun, DM me. We have openings at Flipkart!", post_id=posts[4].id, author_id=alumni5.id),
    Comment(content="Check out our job portal here, I posted some openings.", post_id=posts[4].id, author_id=alumni2.id),

    Comment(content="This is gold! Thank you for sharing! 🙏", post_id=posts[5].id, author_id=student1.id),
    Comment(content="Consistency is truly the key. Great advice Neha!", post_id=posts[5].id, author_id=student2.id),
    Comment(content="Saved this post. Very helpful!", post_id=posts[5].id, author_id=student3.id),
]
db.add_all(comments)
db.commit()

# ===== LIKES =====
print("❤️ Creating likes...")
likes = [
    Like(post_id=posts[0].id, user_id=alumni2.id),
    Like(post_id=posts[0].id, user_id=alumni3.id),
    Like(post_id=posts[0].id, user_id=student1.id),
    Like(post_id=posts[0].id, user_id=admin.id),
    Like(post_id=posts[0].id, user_id=alumni5.id),

    Like(post_id=posts[1].id, user_id=student1.id),
    Like(post_id=posts[1].id, user_id=student2.id),
    Like(post_id=posts[1].id, user_id=alumni1.id),

    Like(post_id=posts[2].id, user_id=alumni5.id),
    Like(post_id=posts[2].id, user_id=student3.id),

    Like(post_id=posts[3].id, user_id=alumni1.id),
    Like(post_id=posts[3].id, user_id=alumni2.id),
    Like(post_id=posts[3].id, user_id=alumni3.id),

    Like(post_id=posts[4].id, user_id=alumni5.id),
    Like(post_id=posts[4].id, user_id=alumni1.id),

    Like(post_id=posts[5].id, user_id=student1.id),
    Like(post_id=posts[5].id, user_id=student2.id),
    Like(post_id=posts[5].id, user_id=student3.id),
    Like(post_id=posts[5].id, user_id=alumni1.id),

    Like(post_id=posts[6].id, user_id=alumni1.id),
    Like(post_id=posts[6].id, user_id=alumni4.id),
]
db.add_all(likes)
db.commit()

# ===== JOB APPLICATIONS =====
print("📄 Creating job applications...")
applications = [
    Application(job_id=jobs[0].id, applicant_id=student1.id, cover_letter="I'm a final year CS student with strong Python skills. I've built REST APIs using FastAPI and Django. I'd love to contribute to Google's backend team.", status="reviewed"),
    Application(job_id=jobs[1].id, applicant_id=student1.id, cover_letter="I have experience building React applications and am familiar with TypeScript. My portfolio includes 3 full-stack projects.", status="pending"),
    Application(job_id=jobs[2].id, applicant_id=student2.id, cover_letter="I'm passionate about cloud computing and have Azure fundamentals certification. This internship would be a perfect learning opportunity.", status="accepted"),
    Application(job_id=jobs[3].id, applicant_id=student3.id, cover_letter="I've completed courses in ML and statistics. I've worked on a recommendation system project during my coursework.", status="pending"),
    Application(job_id=jobs[0].id, applicant_id=student3.id, cover_letter="Strong foundation in Python with experience in Flask and FastAPI. Eager to learn and grow at Google.", status="pending"),
]
db.add_all(applications)
db.commit()

print("\n" + "="*50)
print("✅ SEED DATA LOADED SUCCESSFULLY!")
print("="*50)
print("\n📋 LOGIN CREDENTIALS (password for all: password123)")
print("-"*50)
print(f"{'Role':<10} {'Name':<20} {'Email':<25}")
print("-"*50)
print(f"{'Admin':<10} {'Rahul Sharma':<20} {'admin@alumni.com':<25}")
print(f"{'Alumni':<10} {'Priya Patel':<20} {'priya@alumni.com':<25}")
print(f"{'Alumni':<10} {'Amit Kumar':<20} {'amit@alumni.com':<25}")
print(f"{'Alumni':<10} {'Sneha Reddy':<20} {'sneha@alumni.com':<25}")
print(f"{'Alumni':<10} {'Vikram Singh':<20} {'vikram@alumni.com':<25}")
print(f"{'Alumni':<10} {'Neha Gupta':<20} {'neha@alumni.com':<25}")
for u in more_alumni:
    print(f"{'Alumni':<10} {u.name:<20} {u.email:<25}")
print(f"{'Student':<10} {'Arjun Verma':<20} {'student@alumni.com':<25}")
print(f"{'Student':<10} {'Kavya Nair':<20} {'kavya@alumni.com':<25}")
print(f"{'Student':<10} {'Rohan Mehta':<20} {'rohan@alumni.com':<25}")
for u in more_students:
    print(f"{'Student':<10} {u.name:<20} {u.email:<25}")
print("-"*50)
print(f"\n📊 Created: {len(users)} users, {len(jobs)} jobs, {len(events)} events,")
print(f"   {len(posts)} posts, {len(comments)} comments, {len(likes)} likes, {len(applications)} applications,")
print(f"   {len(connections)} connections")
print(f"\n🌐 Open http://localhost:8000 in your browser")

db.close()
