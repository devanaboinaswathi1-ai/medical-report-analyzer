from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/medical_analyzer")
client = AsyncIOMotorClient(MONGODB_URI)
database = client.medical_analyzer
reports_collection = database.reports
users_collection = database.users

async def create_user(user_data):
    """Save a new user to database"""
    user_data["createdAt"] = datetime.now().isoformat()
    result = await users_collection.insert_one(user_data)
    return str(result.inserted_id)

async def get_user_by_username(username):
    """Find a user by username string"""
    user = await users_collection.find_one({"username": username})
    if user:
        user["_id"] = str(user["_id"])
    return user

async def get_user_by_email(email):
    """Find a user by email string"""
    user = await users_collection.find_one({"email": email})
    if user:
        user["_id"] = str(user["_id"])
    return user

async def save_report(report_data):
    """Save a medical report to database"""
    # Add createdAt timestamp as string (MongoDB compatible)
    report_data["createdAt"] = datetime.now().isoformat()
    
    # MongoDB handles the insertion
    result = await reports_collection.insert_one(report_data)
    return str(result.inserted_id)

async def get_all_reports():
    """Get all reports from database"""
    reports = []
    cursor = reports_collection.find().sort("createdAt", -1)
    async for document in cursor:
        document["_id"] = str(document["_id"])
        reports.append(document)
    return reports

async def get_report_by_id(report_id):
    """Get a specific report by ID"""
    from bson import ObjectId
    try:
        report = await reports_collection.find_one({"_id": ObjectId(report_id)})
        if report:
            report["_id"] = str(report["_id"])
        return report
    except Exception:
        return None

async def delete_report(report_id):
    """Delete a report by ID"""
    from bson import ObjectId
    try:
        result = await reports_collection.delete_one({"_id": ObjectId(report_id)})
        return result.deleted_count > 0
    except Exception:
        return False