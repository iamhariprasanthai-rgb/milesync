
import sys
import os
from sqlmodel import Session, create_engine, select

# Add the parent directory to sys.path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.user import User, AuthProvider
from app.services.auth_service import hash_password

def seed_remote_admin(db_url):
    """Seed admin user into remote database."""
    print(f"Connecting to database...")
    
    # Ensure URL handles postgres protocol correctly for SQLAlchemy
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    try:
        engine = create_engine(db_url)
        
        with Session(engine) as session:
            # Check if admin exists
            admin_email = "admin@milesync.demo"
            existing = session.exec(select(User).where(User.email == admin_email)).first()
            
            if existing:
                print(f"✅ Admin user '{admin_email}' already exists.")
                # Ensure it is a superuser
                if not existing.is_superuser:
                    existing.is_superuser = True
                    session.add(existing)
                    session.commit()
                    print("   Updated to superuser status.")
                return

            print("Creating admin user...")
            admin_user = User(
                email=admin_email,
                name="System Admin",
                password_hash=hash_password("admin123"),
                auth_provider=AuthProvider.EMAIL,
                is_active=True,
                is_superuser=True,
                token_limit=1000000, # Large limit for admin
            )
            session.add(admin_user)
            session.commit()
            print(f"🎉 Successfully created admin user!")
            print(f"   Email: {admin_email}")
            print(f"   Pass:  admin123")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("Tip: Make sure you copied the 'External Database URL' from Render Dashboard.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python seed_remote.py <EXTERNAL_DATABASE_URL>")
        sys.exit(1)
        
    seed_remote_admin(sys.argv[1])
