import pytz
from datetime import date, datetime
import motor.motor_asyncio
from info import DATABASE_NAME, DATABASE_URL, IMDB, IMDB_TEMPLATE, MELCOW_NEW_USERS, P_TTI_SHOW_OFF, SINGLE_BUTTON, SPELL_CHECK_REPLY, PROTECT_CONTENT, MAX_RIST_BTNS, IMDB_DELET_TIME                  

class Database:
    
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users
        self.grp = self.db.groups


    def new_user(self, id, name):
        tz = pytz.timezone('Asia/Kolkata')  # Define tz here
        return dict(
            id=id,
            name=name,
            ban_status=dict(
                is_banned=False,
                ban_reason="",
            ),
            timestamp=datetime.now(tz)
        )

    def new_group(self, id, title, username):
        tz = pytz.timezone('Asia/Kolkata')  # Define tz here
        return dict(
            id=id,
            title=title,
            username=username,
            chat_status=dict(
                is_disabled=False,
                reason="",
            ),
            timestamp=datetime.now(tz)
        )

    async def daily_users_count(self, today):
        tz = pytz.timezone('Asia/Kolkata')
        start = tz.localize(datetime.combine(today, datetime.min.time()))
        end = tz.localize(datetime.combine(today, datetime.max.time()))
        count = await self.col.count_documents({
            'timestamp': {'$gte': start, '$lt': end}
        })
        return count
    
    async def daily_chats_count(self, today):
        tz = pytz.timezone('Asia/Kolkata')
        start = tz.localize(datetime.combine(today, datetime.min.time()))
        end = tz.localize(datetime.combine(today, datetime.max.time()))
        count = await self.grp.count_documents({
            'timestamp': {'$gte': start, '$lt': end}
        })
        return count

    async def save_chat_invite_link(self, chat_id, invite_link):
        await self.grp.update_one({'id': int(chat_id)}, {'$set': {'invite_link': invite_link}})
    
    async def get_chat_invite_link(self, chat_id):
        chat = await self.grp.find_one({'id': int(chat_id)})
        if chat:
            return chat.get('invite_link', None)
        return None

    async def update_verification(self, id, date, time):
        status = {
            'date': str(date),
            'time': str(time)
        }
        await self.col.update_one({'id': int(id)}, {'$set': {'verification_status': status}})
    
    async def get_verified(self, id):
        default = {
            'date': "1999-12-31",
            'time': "23:59:59"
        }
        user = await self.col.find_one({'id': int(id)})
        if user:
            return user.get("verification_status", default)
        return default

    async def add_premium(self, user_id: int, days: int):
        """Add premium to a user for given days"""
        tz = pytz.timezone("Asia/Kolkata")
        start_date = datetime.now(tz)
        end_date = start_date + timedelta(days=days)

        premium_status = {
            "is_premium": True,
            "start_date": str(start_date),
            "end_date": str(end_date)
        }

        await self.col.update_one(
            {"id": int(user_id)},
            {"$set": {"premium_status": premium_status}},
            upsert=True
        )

    async def is_premium(self, user_id: int) -> bool:
        """Check if user is currently premium"""
        tz = pytz.timezone("Asia/Kolkata")
        now = datetime.now(tz)
        user = await self.col.find_one({"id": int(user_id)})
        if not user:
            return False
        premium = user.get("premium_status", {})
        if not premium.get("is_premium"):
            return False
        end_date = datetime.fromisoformat(premium.get("end_date"))
        return now < end_date

    async def remove_premium(self, user_id: int):
        """Remove premium from user"""
        premium_status = {
            "is_premium": False,
            "start_date": None,
            "end_date": None
        }
        await self.col.update_one(
            {"id": int(user_id)},
            {"$set": {"premium_status": premium_status}}
        )

    async def total_premium_users_count(self) -> int:
        """Count all users who have premium field"""
        return await self.col.count_documents({"premium_status.is_premium": True})

    async def total_active_premium_users_count(self) -> int:
        """Count users with active (not expired) premium"""
        tz = pytz.timezone("Asia/Kolkata")
        now = datetime.now(tz)
        return await self.col.count_documents({
            "premium_status.is_premium": True,
            "premium_status.end_date": {"$gt": str(now)}
        })
        
    async def get_premium_days_left(self, user_id: int) -> int:
        """Return how many days of premium are left for a user"""
        tz = pytz.timezone("Asia/Kolkata")
        now = datetime.now(tz)
        user = await self.col.find_one({"id": int(user_id)})
        if not user or "premium_status" not in user:
            return 0
        premium = user["premium_status"]
        if not premium.get("is_premium"):
            return 0
        end_date = datetime.fromisoformat(premium.get("end_date"))
        if now >= end_date:
            return 0
        days_left = (end_date - now).days
        return days_left
        
    async def add_user(self, id, name):
        user = self.new_user(id, name)
        await self.col.insert_one(user)
    
    async def is_user_exist(self, id):
        user = await self.col.find_one({'id':int(id)})
        return bool(user)
    
    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count
    
    async def remove_ban(self, id):
        ban_status = dict(
            is_banned=False,
            ban_reason=''
        )
        await self.col.update_one({'id': id}, {'$set': {'ban_status': ban_status}})
    
    async def ban_user(self, user_id, ban_reason="No Reason"):
        ban_status = dict(
            is_banned=True,
            ban_reason=ban_reason
        )
        await self.col.update_one({'id': user_id}, {'$set': {'ban_status': ban_status}})

    async def get_ban_status(self, id):
        default = dict(
            is_banned=False,
            ban_reason=''
        )
        user = await self.col.find_one({'id':int(id)})
        if not user:
            return default
        return user.get('ban_status', default)

    async def get_all_users(self):
        return self.col.find({})
    
    async def delete_user(self, user_id):
        await self.col.delete_many({'id': int(user_id)})
    
    async def get_banned(self):
        users = self.col.find({'ban_status.is_banned': True})
        chats = self.grp.find({'chat_status.is_disabled': True})
        b_chats = [chat['id'] async for chat in chats]
        b_users = [user['id'] async for user in users]
        return b_users, b_chats
    
    async def add_chat(self, chat, title, username):
        chat = self.new_group(chat, title, username)
        await self.grp.insert_one(chat)
    
    async def get_chat(self, chat):
        chat = await self.grp.find_one({'id':int(chat)})
        return False if not chat else chat.get('chat_status')
    
    async def re_enable_chat(self, id):
        chat_status=dict(
            is_disabled=False,
            reason="",
            )
        await self.grp.update_one({'id': int(id)}, {'$set': {'chat_status': chat_status}})
        
    async def disable_chat(self, chat, reason="No Reason"):
        chat_status=dict(
            is_disabled=True,
            reason=reason,
            )
        await self.grp.update_one({'id': int(chat)}, {'$set': {'chat_status': chat_status}})
    
    async def total_chat_count(self):
        count = await self.grp.count_documents({})
        return count
    
    async def get_all_chats(self):
        return self.grp.find({})

    async def delete_chat(self, chat_id):
        await self.grp.delete_many({'id': int(chat_id)})

    async def get_db_size(self):
        return (await self.db.command("dbstats"))['dataSize']

    async def update_settings(self, id, settings):
        await self.grp.update_one({'id': int(id)}, {'$set': {'settings': settings}})
        
    async def get_settings(self, id):       
        default = {
            'button': SINGLE_BUTTON,
            'botpm': P_TTI_SHOW_OFF,
            'file_secure': PROTECT_CONTENT,
            'imdb': IMDB,
            'spell_check': SPELL_CHECK_REPLY,
            'welcome': MELCOW_NEW_USERS,
            'template': IMDB_TEMPLATE            
        }
        chat = await self.grp.find_one({'id':int(id)})
        if chat:
            return chat.get('settings', default)
        return default

db = Database(DATABASE_URL, DATABASE_NAME)
