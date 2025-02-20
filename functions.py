import re
import pymongo
from pymongo import MongoClient
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import datetime
from bson import ObjectId


class functions(): 
    def __init__(self):
        self.client = MongoClient('mongodb+srv://ivdmahesh:suDQZhpKAwtLALu1@cluster0.7sc7y.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
        self.access_token = '8062158294:AAH0UiWJQO0xWTEMi_PXZqxoV-tgJ7GmxDk'
        self.bot = Bot(token=self.access_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    
    def PhoneIsValid(self,phone):
        if(phone.isdigit() and len(phone) == 10):
            return True
        return False
    
    def CheckPhoneInDb(self,phone):
        regex_pattern = re.compile(f"{phone}$")
        doc = self.client.Cluster0.profile.find_one({'phone':regex_pattern})
        if(doc):
            return doc["userid"]
        return None

    async def SendOtpToUser(self,userid_present, randomint):
        await self.bot.send_message(userid_present, str(randomint)+"- Is your OTP for Inmycolony", parse_mode=ParseMode.MARKDOWN)
    

    def StoreOtpInDb(self,userid_present, randomint):
        self.client.Cluster0.session.create_index([('created_at', pymongo.DESCENDING)], expireAfterSeconds=120)
        document = {
                      "userid": userid_present,
                      "created_at": datetime.datetime.now(datetime.timezone.utc),  # Store current UTC time
                      "data": randomint}
        self.client.Cluster0.session.insert_one(document)

    def GetOTPFromDb(self,userid_present):
        doc = self.client.Cluster0.session.find_one({'userid':userid_present})
        return doc
    
    def CheckIfLikeInDb(self, user, event):
        count = self.client.Cluster0.like.count_documents({'userid':user,'eventid':event})
        bool = False if count == 0 else True
        return bool

    def DeleteLike(self, user, event):
        self.client.Cluster0.like.delete_one({'userid':user,'eventid':event})

    def InsertLike(self, user, event):
        myquery = {"userid": user}
        profile_json = self.client.Cluster0.profile.find_one(myquery)
        document = {
            "userid":user,
            "eventid":event,
            "name":profile_json["name"],
            "description":profile_json["description"],
            "profilepic":profile_json["profilepic"],
            "location":profile_json["location"]
        }
        self.client.Cluster0.like.insert_one(document)

    def InsertComment(self, user, event, comment):
        myquery = {"userid":user}
        profile_json = self.client.Cluster0.profile.find_one(myquery)
        document = {
            "userid":user,
            "eventid":event,
            "comment":comment,
            "name":profile_json["name"],
            "description":profile_json["description"],
            "profilepic":profile_json["profilepic"],
            "location":profile_json["location"],
            "created_at": datetime.datetime.now(datetime.timezone.utc)
        }
        self.client.Cluster0.comment.insert_one(document)

    def GetUserForComment(self, comment):
        document = self.client.Cluster0.comment.find_one({"_id":ObjectId(comment)})
        userid = document["userid"] if document is not None else None
        return userid
    
    def DeleteComment(self, comment):
        self.client.Cluster0.comment.delete_one({"_id":ObjectId(comment)})

    def UpdateComments(self,event):
        count = self.client.Cluster0.comment.count_documents({'eventid':event})
        self.client.Cluster0.event.update_one({'_id':ObjectId(event)},{'$set':{'comments':count}})

    def UpdateLikes(self,event):
        count = self.client.Cluster0.like.count_documents({'eventid':event})
        self.client.Cluster0.event.update_one({'_id':ObjectId(event)},{'$set':{'likes':count}})

    def getUser(self, user):
        myquery = {"userid":user}
        doc = self.client.Cluster0.profile.find_one(myquery)
        return doc
    
    async def getLikes(self, location, event):
        pipeline = [
            {
                "$geoNear": {
                "near": location,  # Point to search near
                "distanceField": "distance",  # Field to store the distance of each result
                "spherical": True,  # Use spherical geometry for the distance calculation
            }
        },
        {
             "$match": {
            "eventid": event  # Replace with your field and value
        }
        },
       {
          "$project": {
                    "_id":0,  
                    "name":1,
                    "description":1,
                    "profilepic":1,
                    "distance":1

        }
        }

        ]
        likes= self.client.Cluster0.like.aggregate(pipeline)
        likes = list(likes)
        return likes

    async def getComments(self, user, location, event):
        pipeline = [
            {
                "$geoNear": {
                "near": location,  # Point to search near
                "distanceField": "distance",  # Field to store the distance of each result
                "spherical": True,  # Use spherical geometry for the distance calculation
            }
        },
        {
             "$match": {
            "eventid": event  # Replace with your field and value
        }
        },
        {
                "$project": {
                    "_id":0,
                    "commentid":{"$toString": "$_id"},
                    "userid":1,
                    "eventid":1,
                    "comment":1,
                    "distance":1,
                    "name":1,
                    "description":1,
                    "profilepic":1,
                    "commentcreationtimeformatted":{
                         "$dateToString": {
                            "format": "%B %d, %Y",  # Desired format: Year-Month-Day Hour:Minute:Second
                            "date": "$created_at"  # Date field to format
                        }
                    }
                }
        },
        {
            "$addFields": {
                "is_same_user": {
                     "$cond": {
                      "if": { "$eq": ["$userid", user] },  # Check if userid column value is same as user
                      "then": True,  # If True, set is_same_user as True
                      "else": False  # If False, set is_same_user as False
                }
            }
        }
    }

        ]
        comments= self.client.Cluster0.comment.aggregate(pipeline)
        comments = list(comments)
        return comments

    async def getEvents(self,location,user):
        events_liked = self.client.Cluster0.like.find({'userid':user},{'_id':0,'eventid':1}) 
        events_liked_list = [event['eventid'] for event in events_liked]
        pipeline = [
            {
                "$geoNear": {
                "near": location,  # Point to search near
                "distanceField": "distance",  # Field to store the distance of each result
                "spherical": True,  # Use spherical geometry for the distance calculation
            }
        },
         {
            "$sort": {
                "eventupdationtime": -1  # -1 means descending order
            }
        },
        {
                "$project": {
                    "_id":0,
                    "eventid":{"$toString": "$_id"},
                    "eventpic":1,
                    "eventtitle":1,
                    "eventtime":1,
                    "eventupdationtimeformatted":{
                         "$dateToString": {
                            "format": "%B %d, %Y",  # Desired format: Year-Month-Day Hour:Minute:Second
                            "date": "$eventupdationtime"  # Date field to format
                        }
                    },
                    "photos":1,
                    "likes":1,
                    "comments":1,
                    "distance":1,
                    "is_liked": {
                "$cond": {
                    "if": {
                        "$in": [{"$toString": "$_id"}, events_liked_list]  # Check if col1 value is in the list
                    },
                    "then": True,  # If True, set is_in_list as True
                    "else": False  # If False, set is_in_list as False
                }
            }
                }
        }]
        events= self.client.Cluster0.event.aggregate(pipeline)
        events = list(events)
        return events



