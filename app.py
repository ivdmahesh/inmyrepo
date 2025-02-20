from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from langchain.agents import initialize_agent

from langchain.agents import AgentType
from langchain_openai import  ChatOpenAI
from langchain_core.tools import tool
import random

from functions import functions

from pydantic import BaseModel

import datetime, math

app = FastAPI()

origins = [
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"]
)

f = functions()
class Message(BaseModel):
    message: str


#send OTP to this number - 9849502694
@tool(return_direct=True)
async def SendOtpGivenPhonenumber(phone:str):
    """ Sends Otp to a given phone number"""
    bool_valid = f.PhoneIsValid(phone)
    if(bool_valid == False):
        return {"message":"Invalid Phone","code":1}
    userid_present = f.CheckPhoneInDb(phone)
    if(userid_present == None):
        return {"message":"Please create profile from inmycolony telegram bot Menu","code":2}
    randomint = random.randint(1000, 9999)
    await f.SendOtpToUser(userid_present, randomint)
    f.StoreOtpInDb(userid_present, randomint)
    return {"message":"Sent OTP","code":3}

#OTP is 1234 and phone number is 9849502694. Verify the phone number.
@tool(return_direct=True)
async def VerifyPhonenumber(otp:str,phone:str):
    """ Verify phone number given otp and phone number """
    bool_valid = f.PhoneIsValid(phone)
    if(bool_valid == False):
        return {"message":"Invalid Phone","code":1}
    userid_present = f.CheckPhoneInDb(phone)
    if(userid_present == None):
        return {"message":"Please create profile from inmycolony telegram bot Menu","code":2}
    otpdoc = f.GetOTPFromDb(userid_present)
    if(otpdoc and str(otpdoc['data'])== otp):
        return {"message":"Verification Successful","code":3,"data":userid_present}
    return {"message":"OTP mismatch","code":4}

# user 5808472767 has put a like for the event 679a37329c453c928eb34fed 
@tool(return_direct=True)
async def Like(user:int, event:str):
    """Store like of user for an event"""
    like_present = f.CheckIfLikeInDb(user, event)
    if(like_present == True):
        f.DeleteLike(user, event)
        f.UpdateLikes(event)
        return {"message":"Like Deleted", "code":1}
    f.InsertLike(user, event)
    f.UpdateLikes(event)
    return {"message":"Like Inserted", "code":2}

# user 5808472767 has commented on event 67989e2bf693ee1fb1049fb3 as following - This is amazing
@tool(return_direct=True)
async def Comment(user: int, event:str, comment:str):
    """Store comment of user for an event"""
    comment_empty = 1 if len(comment.strip()) == 0 else 0
    if(comment_empty):
        return {"message":"comment empty", "code":1}
    f.InsertComment(user,event,comment)
    f.UpdateComments(event)
    return {"message":"Comment Inserted", "code":2}


# user 5808472767 has deleted the comment with id 679a150ee5cc52f65addcfe8 for the event 679a37329c453c928eb34fed
@tool(return_direct=True)
async def DeleteComment(user: int, comment:str, event:str):
    """Delete comment having given id"""
    user_match = f.GetUserForComment(comment)
    if(user_match != user):
        return {"message":"User mismatch", "code":1}
    f.DeleteComment(comment)
    f.UpdateComments(event)
    return {"message":"Comment Deleted", "code":2}

#fetch comments for user with id 5808472767 and event 67a9c524f7408294c58e1abc and page 1
@tool(return_direct=True)
async def FetchComments(user: int, event: str, page: int):
    """Fetch comments for a given user, event and page number"""
    user_doc = f.getUser(user)
    comments = await f.getComments(user,user_doc['location'],event)
    limit = 10
    totalpages = math.ceil(len(comments)/limit)
    if(len(comments)==0):
        skip = -1
    else:
        skip = (page-1)*limit

    skippedItems = comments[skip:]
    takenItems = skippedItems[0:limit]

    if(page*limit>len(comments)):
        to = len(comments)
    else:
        to= page*limit
    message = "Displaying results from "+ str(skip+1) + " to "+str(to) + " of total " + str(len(comments))

    return {"message":message, "data":takenItems, "code":1,"totalpages":totalpages}


#fetch likes for user with id 5808472767 and event 67a9c524f7408294c58e1abc and page 1
@tool(return_direct=True)
async def FetchLikes(user: int, event: str, page: int):
    """Fetch likes for a given user, event and page number"""
    user_doc = f.getUser(user)
    likes = await f.getLikes(user_doc['location'],event)
    limit = 10
    totalpages = math.ceil(len(likes)/limit)
    if(len(likes)==0):
        skip = -1
    else:
        skip = (page - 1)*limit
  
    skippedItems = likes[skip:]
    takenItems = skippedItems[0: limit]

    if(page*limit>len(likes)):
        to = len(likes)
    else:
        to= page*limit
    message = "Displaying results from "+ str(skip+1) + " to "+str(to) + " of total " + str(len(likes))

    return {"message":message, "data":takenItems, "code":1,"totalpages":totalpages}



# fetch page 1 of events for user with id 5808472767
@tool(return_direct=True)
async def FetchEvents(user: int, page: int):
    """Fetch events for a given user and page number"""
    user_doc = f.getUser(user)
    events = await f.getEvents(user_doc['location'],user)
    limit = 4
    totalpages=math.ceil(len(events)/limit)
    if(len(events)==0):
        skip = -1
    else:
        skip = (page - 1)*limit
  
    skippedItems = events[skip:]
    takenItems = skippedItems[0: limit]

    if(page*limit>len(events)):
        to = len(events)
    else:
        to= page*limit
    message = "Displaying results from "+ str(skip+1) + " to "+str(to) + " of total " + str(len(events))

    return {"message":message, "data":takenItems, "code":1,"totalpages":totalpages}


model = ChatOpenAI(

    model_name="gpt-3.5-turbo",
    openai_api_key="sk-proj-QuEhwSwuMWRXOF0687wOT3BlbkFJBDMcMVZ47ZGH3IFICU55",
    temperature=0
)

tools = [SendOtpGivenPhonenumber,VerifyPhonenumber,Like,Comment,DeleteComment,FetchEvents,FetchLikes,FetchComments]
agent = initialize_agent(tools, model, agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION, verbose=True)


@app.post("/chat")
async def chat(message: Message,request: Request):
    result = await agent.arun(message.message)
    return JSONResponse(content=result, status_code=200)

'''
1. otp verification - done
2. fetch events - done
3. like an event - done
4. comment on event - done
5. fetch users who liked event - done
6. fetch comments for event
'''