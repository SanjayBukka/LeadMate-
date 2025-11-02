"""
Quick Password Reset - Just edit the email and password below and run!
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from config import settings

# ============================================================================
# EDIT THESE VALUES:
# ============================================================================
EMAIL_TO_RESET = "Nikunj@woxsen.edu.in"  # <-- Put the email here (Note: Capital N!)
NEW_PASSWORD = "123Nikunj"             # <-- Put new password here
# ============================================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def reset_password():
    """Reset password for the specified email"""
    
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    
    try:
        print("="* 60)
        print("PASSWORD RESET SCRIPT")
        print("=" * 60)
        print(f"\nLooking for user: {EMAIL_TO_RESET}")
        
        # Find user
        user = await db.users.find_one({"email": EMAIL_TO_RESET})
        
        if not user:
            print(f"\n[ERROR] User not found!")
            print("\nAvailable users:")
            async for u in db.users.find():
                print(f"  - {u['email']} ({u['name']}, role: {u['role']})")
            return
        
        print(f"Found: {user['name']} (Role: {user['role']})")
        
        # Hash new password
        print(f"\nHashing new password...")
        new_hash = pwd_context.hash(NEW_PASSWORD)
        
        # Update in database
        print(f"Updating database...")
        result = await db.users.update_one(
            {"email": EMAIL_TO_RESET},
            {"$set": {"hashedPassword": new_hash}}
        )
        
        if result.modified_count > 0:
            print("\n" + "=" * 60)
            print("[SUCCESS] Password Reset Complete!")
            print("=" * 60)
            print(f"Email:    {EMAIL_TO_RESET}")
            print(f"Password: {NEW_PASSWORD}")
            print(f"Role:     {user['role']}")
            print("=" * 60)
            print("\nYou can now login with these credentials!")
        else:
            print("\n[ERROR] Failed to update password")
            
    except Exception as e:
        print(f"\n[ERROR] {e}")
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(reset_password())

