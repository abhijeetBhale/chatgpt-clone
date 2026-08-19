"""Export data from MongoDB to JSON files."""
import json
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "exports")


def export():
    client = MongoClient(MONGO_URL)
    db = client["BoostAI"]

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    chats = list(db.chats.find({}, {"_id": {"$toString": "$_id"}, "userId": 1, "history": 1, "createdAt": 1, "updatedAt": 1}))
    with open(os.path.join(OUTPUT_DIR, "chats.json"), "w") as f:
        json.dump(chats, f, default=str, indent=2)
    print(f"Exported {len(chats)} chats")

    userchats = list(db.userchats.find({}, {"_id": {"$toString": "$_id"}, "userId": 1, "chats": 1, "createdAt": 1, "updatedAt": 1}))
    with open(os.path.join(OUTPUT_DIR, "userchats.json"), "w") as f:
        json.dump(userchats, f, default=str, indent=2)
    print(f"Exported {len(userchats)} userchats documents")

    client.close()
    print(f"Export complete. Files saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    export()
