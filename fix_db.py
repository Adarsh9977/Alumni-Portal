# Fix DB schema for SQLite
import sqlite3
import os

db_path = "alumni_portal.db"
if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        # Check if column exists
        cur.execute("PRAGMA table_info(applications)")
        cols = [col[1] for col in cur.fetchall()]
        if "resume_path" not in cols:
            print("🔧 Adding resume_path to applications table...")
            cur.execute("ALTER TABLE applications ADD COLUMN resume_path VARCHAR(255)")
            conn.commit()
            print("✅ Column added!")
        else:
            print("✅ Column already exists!")
        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("❌ Database not found!")
