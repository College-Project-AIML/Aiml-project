import os
import psycopg2
from pymongo import MongoClient
from dotenv import load_dotenv
import uuid

load_dotenv()

def seed_postgres():
    
    print("🐘 Connecting to PostgreSQL...")
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB", "aiml_core"),
            user=os.getenv("POSTGRES_USER", "admin"),
            password=os.getenv("POSTGRES_PASSWORD", "securepassword"),
            host="127.0.0.1",
            port=os.getenv("POSTGRES_PORT", "5433") 
        )
        cur = conn.cursor()

        # 1. Check if user exists
        email = "test@example.com"
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        existing_user = cur.fetchone()

        if existing_user:
            user_id = existing_user[0]
            print(f"   👤 User exists. Using ID: {user_id}")
        else:
            user_id = str(uuid.uuid4())
            print(f"   👤 Creating NEW User: Avaneesh (ID: {user_id})")
            cur.execute("""
                INSERT INTO users (id, full_name, email, password_hash, role)
                VALUES (%s, %s, %s, %s, %s);
            """, (user_id, "Avaneesh Test", email, "hashed_secret", "citizen"))

        # 2. Insert/Update Profile
        print("   📄 Upserting Profile...")
        cur.execute("""
            INSERT INTO profiles (user_id, state, annual_income, occupation_sector)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE 
            SET annual_income = EXCLUDED.annual_income;
        """, (user_id, "Karnataka", 50000.00, "student"))

        conn.commit()
        cur.close()
        conn.close()
        print("✅ PostgreSQL Seeded Successfully!")
        
    except Exception as e:
        print(f"❌ PostgreSQL Error: {e}")

def seed_mongo():
    print("\n🍃 Connecting to MongoDB...")
    try:
       # ABSOLUTE HARDCODED URI
        uri = "mongodb://admin:securepassword@127.0.0.1:27017/admin?authSource=admin"
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        
        # This line forces the check
        client.admin.command('ping')
        print("   ✅ Connection Verified!")
    
        db = client["aiml_schemes"]
        collection = db["schemes"]

        dummy_scheme = {
            "name": "PM Kaushal Vikas Yojana",
            "ministry": "Skill Development",
            "type": "skill_training",
            "eligibility_rules": { "min_age": 18 },
            "is_active": True
        }

        # Insert if not exists
        if not collection.find_one({"name": dummy_scheme["name"]}):
            collection.insert_one(dummy_scheme)
            print(f"   📜 Created Scheme: {dummy_scheme['name']}")
        else:
            print(f"   📜 Scheme already exists.")
            
        print("✅ MongoDB Seeded Successfully!")

    except Exception as e:
        print(f"❌ MongoDB Error: {e}")

if __name__ == "__main__":
    seed_postgres()
    seed_mongo()