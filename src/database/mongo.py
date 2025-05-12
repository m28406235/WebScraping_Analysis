from pymongo import MongoClient
from pymongo.errors import BulkWriteError
from data.processor import process_data

def save_mongo():
    try:
        cluster = MongoClient("mongodb+srv://amrm08018:ps3Agk06kUVZTh8A@cluster0.qbbbzxv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
        collection = cluster["Web_Scraping"]["Phones"]
        data = process_data()
        if not data.empty:
            for record in data.to_dict(orient="records"):
                collection.update_one(
                    {"Phone Name": record["Phone Name"]},
                    {"$set": record},
                    upsert=True
                )
            print("Data inserted/updated in MongoDB")
        else:
            print("No data to insert into MongoDB")
    except BulkWriteError as bwe:
        print(f"Error inserting into MongoDB (possible duplicates): {bwe}")
    except Exception as e:
        print(f"Error inserting into MongoDB: {e}")