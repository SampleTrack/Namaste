import logging
from datetime import datetime, date, time
import pytz
from pyrogram import Client, emoji, filters
from pyrogram.errors import QueryIdInvalid
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultCachedDocument,
    InlineQuery
)

from database.ia_filterdb import get_search_results
from database.users_chats_db import db
from utils import is_subscribed, get_size, temp, get_verify_status
from info import CACHE_TIME, AUTH_USERS, AUTH_CHANNEL, CUSTOM_FILE_CAPTION, LOG_CHANNEL
from Script import script

logger = logging.getLogger(__name__)
cache_time = 0 if AUTH_USERS or AUTH_CHANNEL else CACHE_TIME

PREMIUM_MODE = True  # Boolean instead of string


async def check_veri(bot, userid):
    try:
        user = await bot.get_users(int(userid))

        # Add user if not in DB
        if not await db.is_user_exist(user.id):
            await db.add_user(user.id, user.first_name)
            await bot.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(user.id, user.mention))

        tz = pytz.timezone('Asia/Kolkata')
        today = date.today()
        now = datetime.now(tz)
        curr_time = now.time()

        status = await get_verify_status(bot, user.id)
        date_var = status.get("date")
        time_var = status.get("time")

        comp_date = date(*map(int, date_var.split('-')))
        comp_time = time(*map(int, time_var.split(":")))

        if comp_date < today or (comp_date == today and comp_time < curr_time):
            return False
        return True

    except Exception as e:
        logger.error(f"❌ Error verifying user {userid}: {e}", exc_info=True)
        await bot.send_message(LOG_CHANNEL, f"⚠️ Error verifying user `{userid}`:\n`{str(e)}`")
        return False


@Client.on_inline_query()
async def answer(bot, query: InlineQuery):
    """Inline query handler following the 5-step rule system."""

    user_id = query.from_user.id

    # Step 1: Check if user is blocked
    if user_id in temp.BANNED_USERS:
        await query.answer(
            results=[],
            cache_time=0,
            switch_pm_text="⚠️ You are not allowed to use this bot.",
            switch_pm_parameter="not_allowed"
        )
        return

    # Step 2: Check if AUTH_CHANNEL is set
    if AUTH_CHANNEL:
        # Step 3: Check subscription
        if not await is_subscribed(bot, query):
            await query.answer(
                results=[],
                cache_time=0,
                switch_pm_text="📢 Join our channel to use this bot.",
                switch_pm_parameter="subscribe"
            )
            return

    # Step 4: Check PREMIUM_MODE
    if PREMIUM_MODE:
        # Step 5: Verify premium user
        if not await check_veri(bot, user_id):
            await query.answer(
                results=[],
                cache_time=0,
                switch_pm_text="💎 Premium Only - ₹99\nTap to Buy Premium",
                switch_pm_parameter="premium"
            )
            return

    # Parse query string
    if '|' in query.query:
        string, file_type = map(str.strip, query.query.split('|', maxsplit=1))
        file_type = file_type.lower()
    else:
        string = query.query.strip()
        file_type = None

    offset = int(query.offset or 0)
    reply_markup = get_reply_markup(query=string)

    # Fetch search results
    files, next_offset, total = await get_search_results(
        string,
        file_type=file_type,
        max_results=10,
        offset=offset
    )

    results = []
    for file in files:
        title = file.file_name
        size = get_size(file.file_size)
        f_caption = file.caption

        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(
                    file_name=title or '',
                    file_size=size or '',
                    file_caption=f_caption or ''
                )
            except Exception as e:
                logger.exception(e)

        if not f_caption:
            f_caption = f"{file.file_name}"

        results.append(
            InlineQueryResultCachedDocument(
                title=file.file_name,
                document_file_id=file.file_id,
                caption=f_caption,
                description=f'Size: {size}\nType: {file.file_type}',
                reply_markup=reply_markup
            )
        )

    # Send search results
    if results:
        switch_pm_text = f"{emoji.FILE_FOLDER} Results - {total}"
        if string:
            switch_pm_text += f" for {string}"
        try:
            await query.answer(
                results=results,
                is_personal=True,
                cache_time=cache_time,
                switch_pm_text=switch_pm_text,
                switch_pm_parameter="start",
                next_offset=str(next_offset)
            )
        except QueryIdInvalid:
            pass
        except Exception as e:
            logger.exception(str(e))
    else:
        switch_pm_text = f'{emoji.CROSS_MARK} No results'
        if string:
            switch_pm_text += f' for "{string}"'
        await query.answer(
            results=[],
            is_personal=True,
            cache_time=cache_time,
            switch_pm_text=switch_pm_text,
            switch_pm_parameter="okay"
        )


def get_reply_markup(query):
    """Return inline search again button."""
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton('Search again', switch_inline_query_current_chat=query)]]
    )
    
