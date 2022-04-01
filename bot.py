#!/usr/bin/env python3


"""Importing"""
# Importing External Packages
from pyrogram import (
    Client,
    filters
)
from pyrogram.types import (
    Update,
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from pyrogram.errors.exceptions.bad_request_400 import (
    PeerIdInvalid,
    UserNotParticipant,
    ChannelPrivate,
    ChatIdInvalid,
    ChannelInvalid
)
from pymongo import MongoClient

# Importing Credentials & Required Data
try:
    from testexp.config import *
except ModuleNotFoundError:
    from config import *

# Importing built-in module
from re import match, search


"""Connecting to Bot"""
app = Client(
    session_name = "RequestTrackerBot",
    api_id = Config.API_ID,
    api_hash = Config.API_HASH,
    bot_token = Config.BOT_TOKEN
)


'''Connecting To Database'''
mongo_client = MongoClient(Config.MONGO_STR)
db_bot = mongo_client['RequestTrackerBot']
collection_ID = db_bot['channelGroupID']


# Regular Expression for #request
requestRegex = "#[rR][eE][qQ][uU][eE][sS][tT] "


"""Handlers"""

# Start & Help Handler
@app.on_message(filters.private & filters.command(["start", "help"]))
async def startHandler(bot:Update, msg:Message):
    botInfo = await bot.get_me()
    await msg.reply_text(
        "<b>Hi, I am a Request Tracker Bot🤖.</b>\nIf you havn't added me in your Group & Channel yet then <b>➕ add me</b> now.\n\n<b>How to Use me?</b>\n\t1. Add me in your Group & Log Channel.\n\t2. Make me admin in both Log Channel & Group.\n\t3. Give permission to Post , Edit & Delete Messages.\n\t4. Now send Group ID & Channel ID in this format <code>/add GroupID ChannelID</code>.\nNow Bot is ready to be used.\n\n<b>Bot made by @UllasTV</b>",
        parse_mode = "html",
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "➕ Add me to your Group",
                        url = f"https://telegram.me/{botInfo.username}?startgroup=true"
                    )
                ]
            ]
        )
    )
    return

# return group id when bot is added to group
@app.on_message(filters.new_chat_members)
async def chatHandler(bot:Update, msg:Message):
    if msg.new_chat_members[0].is_self: # If bot is added
        await msg.reply_text(
            f"Hey😁, Your Group ID is <code>{msg.chat.id}</code>",
            parse_mode = "html"
        )
    return

# return channel id when message/post from channel is forwarded
@app.on_message(filters.forwarded & filters.private)
async def forwardedHandler(bot:Update, msg:Message):
    forwardInfo = msg.forward_from_chat
    if forwardInfo.type == "channel":   # If message forwarded from channel
        await msg.reply_text(
            f"<b>Hey, Your Channel ID is <code>{forwardInfo.id}</code>\n\nJoin @UllasTV for bengali movies and webseries.</b>",
            parse_mode = "html"
        )
    return

# /add handler to add group id & channel id with database
@app.on_message(filters.private & ~filters.edited & filters.command("add"))
async def groupChannelIDHandler(bot:Update, msg:Message):
    message = msg.text.split(" ")
    if len(message) == 3:   # If command is valid
        _, groupID, channelID = message
        try:
            int(groupID)
            int(channelID)
        except ValueError:  # If Ids are not integer type
            await msg.reply_text(
                "<b>Group ID & Channel ID should be integer type😒.</b>",
                parse_mode = "html"
            )
        else:   # If Ids are integer type
            documents = collection_ID.find()
            for document in documents:
                try:
                    document[groupID]
                except KeyError:
                    pass
                else:   # If group id found in database
                    await msg.reply_text(
                    "<b>Your Group ID already Added.</b>",
                    parse_mode = "html"
                    )
                    break
                for record in document:
                    if record == "_id":
                        continue
                    else:
                        if document[record][0] == channelID:    #If channel id found in database
                            await msg.reply_text(
                                "<b>Your Channel ID already Added ✅</b>",
                                parse_mode = "html"
                            )
                            break
            else:   # If group id & channel not found in db
                try:
                    botSelfGroup = await bot.get_chat_member(int(groupID), 'me')
                except (PeerIdInvalid, ValueError):   # If given group id is invalid
                    await msg.reply_text(
                        "<b>😒Group ID is wrong.</b>",
                        parse_mode = "html"
                    )
                except UserNotParticipant:  # If bot is not in group
                    await msg.reply_text(
                        "<b>😁Add me in group and make me admin, then use /add command.</b>",
                        parse_mode = "html"
                    )
                else:
                    if botSelfGroup.status != "administrator":  # If bot is not admin in group
                        await msg.reply_text(
                            "<b>🥲You have not made me admin in your Group yet, Do it first.</b>",
                            parse_mode = "html"
                        )
                    else:   # If bot is admin in group
                        try:
                            botSelfChannel = await bot.get_chat_member(int(channelID), 'me')
                        except (UserNotParticipant, ChannelPrivate):    # If bot not in channel
                            await msg.reply_text(
                                "<b>😁Add me in Channel and make me admin, then use /add.</b>",
                                parse_mode = "html"
                            )
                        except (ChatIdInvalid, ChannelInvalid): # If given channel id is invalid
                            await msg.reply_text(
                                "<b>😒Channel ID is wrong.</b>",
                                parse_mode = "html"
                            )
                        else:
                            if not (botSelfChannel.can_post_messages and botSelfChannel.can_edit_messages and botSelfChannel.can_delete_messages):  # If bot has not enough permissions
                                await msg.reply_text(
                                    "<b>🥲Make sure to give Permissions like Post Messages, Edit Messages & Delete Messages.</b>",
                                    parse_mode = "html"
                                )
                            else:   # Adding Group ID, Channel ID & User ID in group
                                collection_ID.insert_one(
                                    {
                                        groupID : [channelID, msg.chat.id]
                                    }
                                )
                                await msg.reply_text(
                                    "<b>Your Group and Channel has now been added SuccessFully🥳</b>",
                                    parse_mode = "html"
                                )
    else:   # If command is invalid
        await msg.reply_text(
            "<b>Invalid Format😒</b>\nSend Group ID & Channel ID in this format 👇\n<code>/add GroupID ChannelID</code>",
            parse_mode = "html"
        )
    return

# /remove handler to remove group id & channel id from database
@app.on_message(filters.private & ~filters.edited & filters.command("remove"))
async def channelgroupRemover(bot:Update, msg:Message):
    message = msg.text.split(" ")
    if len(message) == 2:   # If command is valid
        _, groupID = message
        try:
            int(groupID)
        except ValueError:  # If group id not integer type
            await msg.reply_text(
                "<b>Group ID</b> should be integer type😒.",
                parse_mode = "html"
            )
        else:   # If group id is integer type
            documents = collection_ID.find()
            for document in documents:
                try:
                    document[groupID]
                except KeyError:
                    continue
                else:   # If group id found in database
                    if document[groupID][1] == msg.chat.id: # If group id, channel id is removing by one who added
                        collection_ID.delete_one(document)
                        await msg.reply_text(
                            "<b>Your Channel ID & Group ID has now been Deleted😢 from our Database.</b>\n\nYou can add them again by using <code>/add GroupID ChannelID</code>.",
                            parse_mode = "html"
                        )
                    else:   # If group id, channel id is not removing by one who added
                        await msg.reply_text(
                            "<b>😒You are not the one who added this Channel ID & Group ID.</b>",
                            parse_mode = "html"
                        )
                    break
            else:   # If group id not found in database
                await msg.reply_text(
                    "<b>Given Group ID is not found in our Database🤔</b></b>",
                    parse_mode = "html"
                )
    else:   # If command is invalid
        await msg.reply_text(
            "<b>Invalid Command😒</b>\n\nSend command in this format👇\n<code>/remove GroupID</code>",
            parse_mode = "html"
        )
    return

# #request handler
@app.on_message(filters.group & ~filters.edited & filters.regex(requestRegex + "(.*)"))
async def requestHandler(bot:Update, msg:Message):
    groupID = str(msg.chat.id)

    documents = collection_ID.find()
    for document in documents:
        try:
            document[groupID]
        except KeyError:
            continue
        else:   # If group id found in database
            channelID = document[groupID][0]
            fromUser = msg.from_user
            mentionUser = f"<a href='tg://user?id={fromUser.id}'>{fromUser.first_name}</a>"
            requestText = f"<b>{msg.message_id} || Request by {mentionUser}</b>\n\n{msg.text}"
            originalMSG = msg.text
            findRegexStr = match(requestRegex, originalMSG)
            requestString = findRegexStr.group()
            contentRequested = originalMSG.split(requestString)[1]
            
            try:
                groupIDPro = groupID.removeprefix(str(-100))
                channelIDPro = channelID.removeprefix(str(-100))
            except AttributeError:
                groupIDPro = groupID[4:]
                channelIDPro = channelID[4:]

            # Sending request in channel
            requestMSG = await bot.send_message(
                int(channelID),
                requestText,
                reply_markup = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "💬 Requested Message",
                                url = f"https://t.me/c/{groupIDPro}/{msg.message_id}"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "🚫 Reject",
                                "reject"
                            ),
                            InlineKeyboardButton(
                                "Done ✅",
                                "done"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "⚠️ Unavailable ⚠️",
                                "unavailable"
                            )
                        ]
                    ]
                )
            )

            replyText = f"<b>👋 Hello {mentionUser} !!\n\n📍 Your Request👇\n<code>{contentRequested}</code>\nhas been submitted to the admins.</b>\n\nNow wait for admins to verify and update your request(s).\n\nYou can check your Request Status Here 👇"

            # Sending message for user in group
            await msg.reply_text(
                replyText,
                parse_mode = "html",
                reply_to_message_id = msg.message_id,
                reply_markup = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "⏳ Request Status ⏳",
                                url = f"https://t.me/c/{channelIDPro}/{requestMSG.message_id}"
                            )
                        ]
                    ]
                )
            )
            break
    return
        
# callback buttons handler
@app.on_callback_query()
async def callBackButton(bot:Update, callback_query:CallbackQuery):
    channelID = str(callback_query.message.chat.id)

    documents = collection_ID.find()
    for document in documents:
        for key in document:
            if key == "_id":
                continue
            else:
                if document[key][0] != channelID:
                    continue
                else:   # If channel id found in database
                    groupID = key

                    data = callback_query.data  # Callback Data
                    if data == "rejected":
                        return await callback_query.answer(
                            "This request has been rejected.\nAsk admins in group for more info.",
                            show_alert = True
                        )
                    elif data == "completed":
                        return await callback_query.answer(
                            "This request has been Completed 🥳",
                            show_alert = True
                        )
                    user = await bot.get_chat_member(int(channelID), callback_query.from_user.id)
                    if user.status not in ("administrator", "creator"): # If accepting, rejecting request tried to be done by neither admin nor owner
                        await callback_query.answer(
                            "Who the hell are you?\nYour are not an Admin😒.",
                            show_alert = True
                        )
                    else:   # If accepting, rejecting request tried to be done by either admin or owner
                        if data == "reject":
                            result = "REJECTED"
                            groupResult = "has been Rejected 💔"
                            button = InlineKeyboardButton("Request Rejected 🚫", "rejected")
                        elif data == "done":
                            result = "COMPLETED"
                            groupResult = "has been Completed 🥳"
                            button = InlineKeyboardButton("Request Completed✅", "completed")
                        elif data == "unavailable":
                            result = "UNAVAILABLE"
                            groupResult = "is not available currently 🥲"
                            button = InlineKeyboardButton("Request unavailable 🚫", "rejected")

                        msg = callback_query.message
                        userid = 12345678
                        for m in msg.entities:
                            if m.type == "text_mention":
                                userid = m.user.id
                                userfirstname= m.user.first_name
                        originalMsg = msg.text
                        findRegexStr = search(requestRegex, originalMsg)
                        requestString = findRegexStr.group()
                        contentRequested = originalMsg.split(requestString)[1]
                        requestedBy = originalMsg.removeprefix("Request by ").split('\n\n')[0]
                        messageId = originalMsg.split(' ||')[0]
                        groupIDPro = groupID.removeprefix(str(-100))
                        mentionUser = f"<a href='tg://user?id={userid}'>{requestedBy}</a>"
                        mentionUserNew = f"<a href='tg://user?id={userid}'>{userfirstname}</a>"
                        originalMsgMod = originalMsg.replace(requestedBy, mentionUser)
                        originalMsgMod = f"<s>{originalMsgMod}</s>"
                        msg_link_button = InlineKeyboardButton("Go to the Message", url = f"https://t.me/c/{groupIDPro}/{messageId}") #may occur error sometimes if not supergroups

                        newMsg = f"<b>{result}</b>\n\n{originalMsgMod}"

                        # Editing reqeust message in channel
                        await callback_query.edit_message_text(
                            newMsg,
                            parse_mode = "html",
                            reply_markup = InlineKeyboardMarkup(
                                [
                                    [
                                        button
                                    ],
                                    [
                                        msg_link_button
                                    ]
                                ]
                            )
                        )

                        # Result of request sent to group
                        replyText = f"<b>Dear {mentionUserNew}!!</b>\n\nYour request for\n<code>{contentRequested}</code>\n <b>{groupResult}</b>\n\nJoin @UllasTV for more updates!"
                        await bot.send_message(
                            int(groupID),
                            replyText,
                            parse_mode = "html",
                            reply_to_message_id = int(messageId)
                        )
                    return
    return


"""Bot is Started"""
print("Bot has been Started!!!")
app.run()
