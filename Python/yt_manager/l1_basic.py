import json

def load_data() :
    try :
        with open('youtube.txt', 'r') as file :
            return json.load(file)
    except FileNotFoundError:
        return []

def save_data_helper(videos) :
    with open('youtube.txt', 'w') as file :
        json.dump(videos, file)

def list_all_videos(videos) :
    print('\n')
    print("*" * 40)
    for index, video in enumerate(videos, start=1) :
        print(f"{index}. {video['name']} , Duration : {video['time']}")

def add_video(videos) :
    name = input ("Enter video name : ")
    time = input ("Enter video time : ")
    videos.append({'name': name, 'time': time})
    save_data_helper(videos)

def update_video(videos) :
    list_all_videos(videos)
    index = int(input("Enter video number to update : "))
    if index >= 1 and index <= len(videos) :
        name = input("Enter the new video name : ")
        time = input("Enter the new video time : ")
        videos[index-1] = {'name' : name , 'time' : time}
        save_data_helper(videos)
    else :
        print("Invalid index selected")

def delete_video(videos) :
    list_all_videos(videos)
    index = int(input("Enter video number to delete : "))
    if index >= 1 and index <= len(videos) :
        del videos[index-1]
        save_data_helper(videos)
    else :
        print("Invalid index of video selected.")

def main () :

    videos = load_data()

    while (1) :
        print("\n Youtube Manager | Choose an option")
        print("1. List all video")
        print("2. Add a youtube video")
        print("3. Update a video detail")
        print("4. Delete a video")
        print("4. Exit the app")
        
        choice = input ("Enter your choice : ")
        
        print(videos)
        
        match choice :
            case "1" :
                list_all_videos(videos)
            case "2" :
                add_video(videos)
            case "3" :
                update_video(videos)
            case "4" :
                delete_video(videos)
            case "5" :
                break
            case _ :
                print("Invalid Choice")
                
if __name__ == "__main__" :
    main()
