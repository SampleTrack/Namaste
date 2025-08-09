import logging
import asyncio
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
from utils import is_subscribed, get_size, temp, check_verification
from info import CACHE_TIME, AUTH_USERS, AUTH_CHANNEL, CUSTOM_FILE_CAPTION, LOG_CHANNEL, PREMIUM_MODE
from Script import script

logger = logging.getLogger(__name__)

# Updated cache_time logic: if premium mode is on, always set to 0 (no caching)
cache_time = 0 if (AUTH_USERS or AUTH_CHANNEL or PREMIUM_MODE) else CACHE_TIME


@Client.on_inline_query()
async def answer(bot, query: InlineQuery):
    """Inline query handler with QueryIdInvalid fix and timeout control."""

    user_id = query.from_user.id

    # Step 1: Blocked user check
    if user_id in temp.BANNED_USERS:
        await safe_answer(query,
                          results=[],
                          cache_time=0,
                          switch_pm_text="⚠️ You are not allowed to use this bot.",
                          switch_pm_parameter="not_allowed")
        return

    # Step 2: AUTH_CHANNEL check
    if AUTH_CHANNEL:
        # Step 3: Subscription check
        if not await is_subscribed(bot, query):
            await safe_answer(query,
                              results=[],
                              cache_time=0,
                              switch_pm_text="📢 Join our channel to use this bot.",
                              switch_pm_parameter="subscribe")
            return

    # Step 4: PREMIUM_MODE check
    if PREMIUM_MODE:
        # Step 5: Premium verification
        if not await check_verification(bot, user_id):
            await safe_answer(query,
                              results=[],
                              cache_time=0,
                              switch_pm_text="💎 Premium Only - ₹99\nTap to Buy Premium",
                              switch_pm_parameter="premium")
            return

    # Handle search parameters
    if '|' in query.query:
        string, file_type = query.query.split('|', maxsplit=1)
        string = string.strip()
        file_type = file_type.strip().lower()
    else:
        string = query.query.strip()
        file_type = None

    offset = int(query.offset or 0)
    reply_markup = get_reply_markup(query=string)

    # DB Search with timeout
    try:
        files, next_offset, total = await asyncio.wait_for(
            get_search_results(string, file_type=file_type, max_results=10, offset=offset),
            timeout=4  # Prevents query expiration
        )
    except asyncio.TimeoutError:
        await safe_answer(query,
                          results=[],
                          cache_time=0,
                          switch_pm_text="⏳ Search took too long, try again.",
                          switch_pm_parameter="timeout")
        return
    except Exception as e:
        logger.exception("Search error: %s", e)
        await safe_answer(query,
                          results=[],
                          cache_time=0,
                          switch_pm_text="⚠️ Error during search.",
                          switch_pm_parameter="error")
        return

    # Build results
    results = []
    for file in files:
        title = file.file_name
        size = get_size(file.file_size)
        f_caption = file.caption or file.file_name

        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(
                    file_name=title or "",
                    file_size=size or "",
                    file_caption=f_caption or ""
                )
            except Exception as e:
                logger.exception(e)

        results.append(
            InlineQueryResultCachedDocument(
                title=title,
                document_file_id=file.file_id,
                caption=f_caption,
                description=f'Size: {size}\nType: {file.file_type}',
                reply_markup=reply_markup
            )
        )

    # Prepare switch_pm_text
    if results:
        switch_pm_text = f"{emoji.FILE_FOLDER} Results - {total}"
    else:
        switch_pm_text = f'{emoji.CROSS_MARK} No results'

    if string:
        switch_pm_text += f" for {string}"

    # Send final answer safely
    await safe_answer(query,
                      results=results,
                      is_personal=True,
                      cache_time=cache_time,
                      switch_pm_text=switch_pm_text,
                      switch_pm_parameter="start",
                      next_offset=str(next_offset))


def get_reply_markup(query):
    """Creates reply markup for inline search results."""
    buttons = [
        [InlineKeyboardButton('Search again', switch_inline_query_current_chat=query)]
    ]
    return InlineKeyboardMarkup(buttons)


async def safe_answer(query, **kwargs):
    """Safe wrapper to avoid QueryIdInvalid errors."""
    try:
        await query.answer(**kwargs)
    except QueryIdInvalid:
        logging.warning("Query expired before answering.")
    except Exception as e:
        logging.exception("Error answering inline query: %s", e)
        
