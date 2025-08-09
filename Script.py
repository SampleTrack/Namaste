class script(object):
    START_TXT = """\
<b>👋 Hello {},

My Name Is <a href="https://t.me/{}">{}</a> 🎬
I Can Provide Movies! Just Add Me To Your Group And Enjoy 😍...</b>"""

    HELP_TXT = """\
<b>🆘 Hey {},

Here Is The Help For My Commands.</b>"""

    ABOUT_TXT = """\
<b>✯ My Name: {}
✯ Developer: <a href="https://t.me/iPepkornUpdate">ɪPᴇᴘᴋᴏʀɴUᴘᴅᴀᴛᴇ</a>
✯ Coded On: Python / Pyrogram
✯ My Database: MongoDB
✯ My Server: Anywhere
✯ My Version: iPepkornAlphaBot v10.0.0</b>"""

    SOURCE_TXT = """\
<b>⚠️ NOTE:</b>
- Source Code is Private 🔒</b>"""

    FILE_TXT = """\
<b>📂 Help For File Store</b>

<i>By Using This Module You Can Store Files In My Database And I Will Give You A Permanent Link To Access The Saved Files.
If You Want To Add Files From A Public Channel, Send The File Link Only.
If You Want To Add Files From A Private Channel, You Must Make Me Admin On The Channel To Access Files.</i>

<b>⪼ Commands & Usage</b>
➪ /link › Reply To Any Media To Get The Link
➪ /batch › To Create Links For Multiple Media

<b>⪼ Example:</b>
<code>/batch https://t.me/iPepkornUpdate/1 https://t.me/iPepkornUpdate/10</code>
"""

    FILTER_TXT = "✨ Select Which One You Want... ✨"

    GLOBALFILTER_TXT = """\
<b>🌍 Help For Global Filters</b>

<i>Filter is a feature where users can set automated replies for a particular keyword, and the bot will respond whenever the keyword is found in the message.</i>

<b>Note:</b>
This module only works for my admins.

<b>Commands and Usage:</b>
• /gfilter - To Add Global Filters
• /gfilters - To View List Of All Global Filters
• /delg - To Delete A Specific Global Filter
• /delallg - To Delete All Global Filters

• Use <code>/g_filter off</code> + on/off in your group to control global filter in your group.
"""

    MANUELFILTER_TXT = """\
<b>⚙️ Help For Filters</b>

<i>Filter is a feature where users can set automated replies for a particular keyword, and the bot will respond whenever the keyword is found in the message.</i>

<b>Note:</b>
1. This bot should have admin privileges.
2. Only admins can add filters in a chat.
3. Alert buttons have a limit of 64 characters.

<b>Commands And Usage:</b>
• /filter - Add A Filter In Chat
• /filters - List All The Filters Of A Chat
• /del - Delete A Specific Filter In Chat
• /delall - Delete The Whole Filters In A Chat (Chat Owner Only)

• Use <code>/g_filter off</code> + on/off in your group to control global filter in your group.
"""

    BUTTON_TXT = """\
<b>🔘 Help For Buttons</b>

<i>This bot supports both URL and alert inline buttons.</i>

<b>Note:</b>
1. Telegram will not allow you to send buttons without any content, so content is mandatory.
2. This bot supports buttons with any Telegram media type.
3. Buttons should be properly parsed as markdown format.

<b>URL Buttons:</b>
[Button Text](buttonurl:xxxxxxxxxxxx)

<b>Alert Buttons:</b>
[Button Text](buttonalert:This Is An Alert Message)
"""

    AUTOFILTER_TXT = """\
<b>🤖 Help For AutoFilter</b>

<i>AutoFilter automatically filters & saves files from channel to group. You can use the following commands to on/off the AutoFilter in your group.</i>

• /autofilter on - Enable AutoFilter in your chat
• /autofilter off - Disable AutoFilter in your chat

<b>Other Commands:</b>
• /set_template - Set IMDb Template For Your Group
• /get_template - Get Current IMDb Template For Your Group
"""

    CONNECTION_TXT = """\
<b>🔗 Help For Connections</b>

<i>Used To Connect Bot To PM For Managing Filters. It Helps To Avoid Spamming In Groups.</i>

<b>Note:</b>
• Only admins can add a connection.
• Send /connect to connect me to your PM.

<b>Commands And Usage:</b>
• /connect - Connect A Particular Chat To Your PM
• /disconnect - Disconnect From A Chat
• /connections - List All Your Connections
"""

    ADMIN_TXT = """\
<b>🛠 Help For Admins</b>

<i>This module only works for my admins.</i>

<b>Commands & Usage:</b>
• /logs - To Get The Recent Errors
• /delete - To Delete A Specific File From DB
• /deleteall - To Delete All Files From DB
• /users - To Get List Of My Users And IDs
• /chats - To Get List Of My Chats And IDs
• /channel - To Get List Of Total Connected Channels
• /broadcast - To Broadcast A Message To All Users
• /group_broadcast - To Broadcast A Message To All Connected Groups
• /leave - With Chat ID To Leave From A Chat
• /disable - With Chat ID To Disable A Chat
• /invite - With Chat ID To Get The Invite Link Of Any Chat Where The Bot Is Admin
• /ban_user - With ID To Ban A User
• /unban_user - With ID To Unban A User
• /restart - To Restart The Bot
• /clear_junk - Clear All Deleted & Blocked Accounts In Database
• /clear_junk_group - Clear Added Removed Or Deactivated Groups On DB
"""

    STATUS_TXT = """\
<b>◉ Total Files: <code>{}</code>
◉ Total Users: <code>{}</code>
◉ Total Chats: <code>{}</code>
◉ Used DB Size: <code>{}</code>
◉ Free DB Size: <code>{}</code></b>"""

    LOG_TEXT_G = """\
#NewGroup 😎

Group: {a}
Group ID: <code>{b}</code>
Group Username: @{c}

Total Members: <code>{d}</code>
Total Groups: <code>{e}</code>
Today Groups: <code>{f}</code>

Date: <code>{g}</code>
Time: <code>{h}</code>

Added By: {i}
By {j}

#{k}
#Chats_{k}
"""

    LOG_TEXT_P = """\
#NewUser 😀

ID: <code>{a}</code>
Name: {b}
Username: @{c}

Total Users: {d}
Today Users: {e}

Date: <code>{f}</code>
Time: <code>{g}</code>

By {h}

#{i}
#Users_{i}
"""

    NEW_MEMBER = """\
#NewMember 😀

Group = {a}
Group ID = <code>{b}</code>
Group Username = @{c}
Total Members = <code>{d}</code>
Invite = {e}

Member = {f}
Member ID = <code>{g}</code>
Member Username = @{h}

Date = <code>{i}</code>
Time = <code>{j}</code>

#{k}
#NewMem_{k}
"""

    LEFT_MEMBER = """\
#LeftMember 😔

Group = {a}
Group ID = <code>{b}</code>
Group Username = @{c}
Total Members = <code>{d}</code>
Invite = {e}

Member = {f}
Member ID = <code>{g}</code>
Member Username = @{h}

Date = <code>{i}</code>
Time = <code>{j}</code>

#{k}
#LeftMem_{k}
"""

    REPORT_TXT = """\
#Daily_Report

Date = {a}
Time = {c}

Total
Total Users = <code>{d}</code>
Total Chats = <code>{e}</code>

Yesterday
{b} Users = <code>{f}</code>
{b} Chats = <code>{g}</code>

#{h}
#Report_{h}
"""

    GROUPMANAGER_TXT = """\
<b>🛡 Help For Group Manager</b>

<i>This is help for managing your group. This will work only for group admins.</i>

<b>Commands & Usage:</b>
• /inkick - Kick members with required arguments.
• /instatus - Check current status of chat members.
• /dkick - Kick deleted accounts.
• /ban - To ban a user from the group.
• /unban - To unban a banned user.
• /tban - Temporarily ban a user.
• /mute - To mute a user.
• /unmute - To unmute the muted user.
• /tmute - Mute up to a particular time (e.g., <code>/tmute 2h</code>). Valid values: m/h/d.
• /pin - To pin a message in your chat.
• /unpin - To unpin message in your chat.
• /purge - Delete all messages from the replied message to the current message.
"""

    EXTRAMOD_TXT = """\
<b>✨ Help For Extra Module</b>

<i>Just send any image to edit the image ✨</i>

<b>Commands & Usage:</b>
• /id - Get ID of a specified user
• /info - Get information about a user
• /imdb - Get film info from IMDB source
• /paste [text] - Paste the given text on Pasty
• /tts [text] - Convert text to speech
• /telegraph - Send this command reply with picture or video under 5MB
• /json - Reply with any message to get message info (useful for groups)
• /written - Reply with text to get file (useful for coders)
• /carbon - Reply with text to get carbonated image
• /font [text] - Change your text fonts to fancy fonts
• /share - Reply with text to get text shareable link
• /song [name] - Search the song on YouTube
• /video [link] - Download the YouTube video
"""

    CREATOR_REQUIRED = "❗ <b>You Have To Be The Group Creator To Do That</b>"

    INPUT_REQUIRED = "❗ **Argument Required**"

    KICKED = "✔️ Successfully Kicked {} Members According To The Arguments Provided"

    START_KICK = "Removing inactive members... This may take a while."

    ADMIN_REQUIRED = "❗ <b>I am not admin in this chat, please add me again with all admin permissions.</b>"

    DKICK = "✔️ Kicked {} Deleted Accounts Successfully"

    FETCHING_INFO = "<b>⏳ Please wait, I will fetch all info...</b>"

    SERVER_STATS = """\
Server Stats:

Uptime: {}
CPU Usage: {}%
RAM Usage: {}%
Total Disk: {}
Used Disk: {} ({}%)
Free Disk: {}
"""

    BUTTON_LOCK_TEXT = "Hey {query}\nThis is not for you. Please search yourself."

    FORCE_SUB_TEXT = "Sorry bro, you have not joined my channel yet. Please click the join button to join my channel and try again."

    WELCOME_TEXT = """\
👋 Hey {user} 💞

Welcome to {chat}!

Share & support, request the movies you want 🍿
"""

    IMDB_TEMPLATE = """\
<b>🔎 Query: {query}</b>

🏷 Title: <a href="{url}">{title}</a>
🎭 Genres: {genres}
📆 Year: <a href="{url}/releaseinfo">{year}</a>
🌟 Rating: <a href="{url}/ratings">{rating}</a>/10
"""

    FILE_MSG = """\
<b>Hai 👋 {username}</b> 😍

<b>📫 Your File is Ready</b>

<b>📂 File Name:</b> <code>{filename}</code>
<b>⚙️ File Size:</b> <b>{filesize}</b>
"""

    CHANNEL_CAP = """\
<b>Hai 👋 {}</b> 😍

<code>{}</code>

<b>⚠️ Due to copyright, the file will be deleted from here in 10 minutes. Please download after moving from here to somewhere else!</b>

<b>© Powered by {}</b>
"""

    VERIFY_MSG = """\
Hey {username} 💕

Temporary Token has expired! Kindly generate a new temp token to start using the bot again and get access to unlimited movies for the next 12 hours.

⏰ Validity: 12 hours
"""

    VERIFY_SUC = """\
🎉 Congratulations {username}! Ads Token refreshed successfully!

Now enjoy the bot without any ads and access unlimited movies for the next 12 hours.

⏳ It will expire after 12 hours.
"""

    VERI_MSG = """
🚫 You are not verified! Please verify your account to access unlimited movies for the next 12 hours. 🎬

📋 Copy the link below and paste it into your Chrome browser. Complete the required task to enjoy 12 hours of uninterrupted and ad-free access! ✨🍿
"""

    PREMIUM_TXT = """
✨ <b>Premium Membership - Only ₹99</b> ✨

💥 Get access to exclusive features:
✅ Use Inline Search (Super Fast ⚡)
✅ Ad-Free Experience 🧹
✅ Priority Support 💬
✅ Instant File Access 🔓

🎁 <b>To Upgrade:</b>
Send ₹99 via UPI to: <code>Soon</code>
Then send payment screenshot to @MyselfPrincess

We'll activate your premium within 5 minutes! 💖
"""
    
    RESTART_TXT = """\
🔄 #Restarted

Bot Restarted!
📅 Date: <code>{a}</code>
⏰ Time: <code>{b}</code>
🌐 Timezone: <code>Asia/Kolkata</code>

#{c}
#Restart_{c}
"""
