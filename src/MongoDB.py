from pymongo import MongoClient
from data_processing import get_processed_phone_data

# MongoDB connection
cluster = MongoClient("mongodb+srv://amrm08018:ps3Agk06kUVZTh8A@cluster0.qbbbzxv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = cluster["Web_Scraping"] # database name
collection = db["Phones"] # collection name

# check null values
phone_data=get_processed_phone_data()
print(phone_data.isnull().sum())

# dataframe to dictionary
phone_data_dict = phone_data.to_dict(orient="records")

# Enter the data into MongoDB
try:
    collection.insert_many(phone_data_dict)
    print("Data inserted successfully into MongoDB!")
except Exception as e:
    print(f"An error occurred: {e}")