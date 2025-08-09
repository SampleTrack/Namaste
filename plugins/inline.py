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

        # Timezone and current date/time
        tz = pytz.timezone('Asia/Kolkata')
        today = date.today()
        now = datetime.now(tz)
        curr_time = now.time()

        # Get stored verification status
        status = await get_verify_status(bot, user.id)
        date_var = status.get("date")
        time_var = status.get("time")

        comp_date = date(*map(int, date_var.split('-')))
        comp_time = time(*map(int, time_var.split(":")))

        # Check validity
        if comp_date < today or (comp_date == today and comp_time < curr_time):
            return False
        return True


    except Exception as e:
        logger.error(f"❌ Error occurred while verifying user {userid}: {e}", exc_info=True)
        await bot.send_message(LOG_CHANNEL, f"⚠️ Error verifying user `{userid}`:\n`{str(e)}`")
        return False


async def inline_users(query: InlineQuery):
    """Check if user is allowed to use inline mode."""
    if AUTH_USERS:
        return query.from_user and query.from_user.id in AUTH_USERS
    return query.from_user and query.from_user.id not in temp.BANNED_USERS


@Client.on_inline_query()
async def answer(bot, query: InlineQuery):
    """Show search results for given inline query."""

    # Check inline user permission
    if not await inline_users(query):
        await query.answer(
            results=[],
            cache_time=0,
            switch_pm_text="⚠️ You are not allowed to use this bot.",
            switch_pm_parameter="not_allowed"
        )
        return

    # Check subscription
    if AUTH_CHANNEL and not await is_subscribed(bot, query):
        await query.answer(
            results=[],
            cache_time=0,
            switch_pm_text='📢 Join our channel to use this bot.',
            switch_pm_parameter="subscribe"
        )
        return

    # Premium verification
    if PREMIUM_MODE and not await check_veri(bot, query.from_user.id):
        await query.answer(
            results=[],
            cache_time=0,
            switch_pm_text="💎 Premium Only - ₹99\nTap to Buy Premium",
            switch_pm_parameter="premium"
        )
        return

    # Parse query
    if '|' in query.query:
        string, file_type = map(str.strip, query.query.split('|', maxsplit=1))
        file_type = file_type.lower()
    else:
        string = query.query.strip()
        file_type = None

    offset = int(query.offset or 0)
    reply_markup = get_reply_markup(query=string)

    # Fetch results
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

    # Send results
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
