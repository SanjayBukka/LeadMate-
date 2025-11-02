"""
Password Reset Utility Script
Run this script to reset a user's password in the database
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def reset_user_password(email: str, new_password: str):
    """Reset a user's password by email"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    
    try:
        # Find user by email
        user = await db.users.find_one({"email": email})
        
        if not user:
            print(f"[ERROR] User with email '{email}' not found!")
            return False
        
        # Hash new password
        new_hashed_password = pwd_context.hash(new_password)
        
        # Update password in database
        result = await db.users.update_one(
            {"email": email},
            {"$set": {"hashedPassword": new_hashed_password}}
        )
        
        if result.modified_count > 0:
            print(f"[SUCCESS] Password reset successful for {user['name']} ({email})")
            print(f"Email: {email}")
            print(f"New Password: {new_password}")
            return True
        else:
            print(f"[ERROR] Failed to update password")
            return False
            
    except Exception as e:
        print(f"[ERROR] {e}")
        return False
    finally:
        client.close()


async def list_all_users():
    """List all users in the database"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    
    try:
        print("\nAll Users in Database:")
        print("-" * 80)
        
        async for user in db.users.find():
            print(f"Name: {user['name']}")
            print(f"Email: {user['email']}")
            print(f"Role: {user['role']}")
            print(f"Active: {user.get('isActive', True)}")
            print("-" * 80)
            
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        client.close()


async def main():
    print("=" * 80)
    print("PASSWORD RESET UTILITY")
    print("=" * 80)
    print()
    
    # List all users first
    await list_all_users()
    
    print("\n" + "=" * 80)
    print("Enter user email and new password:")
    print("=" * 80)
    
    # Get input from user
    email = input("Email: ").strip()
    new_password = input("New Password: ").strip()
    
    if not email or not new_password:
        print("[ERROR] Email and password cannot be empty!")
        return
    
    if len(new_password) < 8:
        print("[ERROR] Password must be at least 8 characters!")
        return
    
    # Confirm
    confirm = input(f"\n[WARNING] Reset password for {email}? (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        await reset_user_password(email, new_password)
    else:
        print("[CANCELLED] Password reset cancelled")


if __name__ == "__main__":
    asyncio.run(main())

