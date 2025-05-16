from pymongo import MongoClient
import os

# MongoDB connection URI
MONGO_URI = "mongodb+srv://introgycursor:olaabdel88@introgy.nvg6b5l.mongodb.net/Introgy-Users?retryWrites=true&w=majority&appName=Introgy"

def main():
    # Connect to MongoDB with SSL settings
    client = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True)
    db = client['Introgy-Users']
    
    # List all collections
    print("Current collections in the database:")
    collections = db.list_collection_names()
    for collection in collections:
        print(f"- {collection}")
        # Print count of documents in each collection
        count = db[collection].count_documents({})
        print(f"  Documents count: {count}")
    
    # Ask for confirmation before deletion
    confirmation = input("\nDo you want to delete all documents from these collections? (yes/no): ")
    if confirmation.lower() == 'yes':
        for collection in collections:
            result = db[collection].delete_many({})
            print(f"Cleared {result.deleted_count} documents from collection: {collection}")
        print("\nAll documents have been deleted while preserving the collections.")
    else:
        print("\nOperation cancelled. No documents were deleted.")
    
    client.close()

if __name__ == "__main__":
    main() 