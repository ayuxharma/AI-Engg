from pymongo import MongoClient
from bison import ObjectId

# not a good way to handle ssl
client = MongoClient("xxx", tlsAllowInvalidCertificates=True)

db = client['ytmanager']

video_collection = db['videos']

print(video_collection)

def add_video(name, time) :
    video_collection.insert_one({"name" : name, "time" : time})

def list_videos() :
    for vid in video_collection.find() :
        print(f"ID : {vid['_id']}, Name : {vid['name']} and Time :{vid['time']}")
    
def update_video(video_id, new_name, new_time) :
    video_collection.update_one(
        {'_id' : ObjectId(video_id)}, 
        {'$set' : {"name" : new_name, "time": new_time}}
    )

def delete_video(video_id) :
    video_collection.delete_one({"_id" : ObjectId(video_id)})

def main() :
    while True :
        print(" \n YT manager App")
        print("1. List all videos")
        print("2. Add new video")
        print("3. Update a video")
        print("4. Delete a video")
        print("5. Exit the app")
        
        choice = input("Enter your choice : ")
        
        if choice == '1' :
            list_videos()
        elif choice == '2' :
            name = input("Enter video name : ")
            time = input("Enter video time : ")
            add_video(name, time)
        elif choice == '3' :
            name = input("Enter updated video name : ")
            video_id = input("Enter updated video id : ")
            time = input("Enter updated video time : ")
            update_video(video_id, name, time)
        elif choice == '4' :
            video_id = input("Enter video id to delete : ")
            delete_video(video_id)
        elif choice == '5' :
            break ;
        else :
            print("Invalid choice")

if __name__ == "__main__" :
    main()
