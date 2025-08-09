import logging
from pyrogram import Client, emoji, filters
from pyrogram.errors.exceptions.bad_request_400 import QueryIdInvalid
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultCachedDocument,
    InlineQuery
)
from database.ia_filterdb import get_search_results
from utils import is_subscribed, get_size, temp
from info import CACHE_TIME, AUTH_USERS, AUTH_CHANNEL, CUSTOM_FILE_CAPTION, REQ_CHANNEL

logger = logging.getLogger(__name__)
cache_time = 0 if AUTH_USERS or AUTH_CHANNEL else CACHE_TIME


async def inline_users(query: InlineQuery):
    if AUTH_USERS:
        return query.from_user and query.from_user.id in AUTH_USERS
    return query.from_user and query.from_user.id not in temp.BANNED_USERS


def get_reply_markup(query):
    buttons = [
        [InlineKeyboardButton('🔍 Search again', switch_inline_query_current_chat=query)]
    ]
    return InlineKeyboardMarkup(buttons)


@Client.on_inline_query()
async def answer(bot, query):
    """Show search results for given inline query"""

    try:
        # Check user authorization
        if not await inline_users(query):
            await query.answer(
                results=[],
                cache_time=0,
                switch_pm_text='🚫 Access Denied',
                switch_pm_parameter="unauthorized"
            )
            return

        # Check subscription requirement
        if (AUTH_CHANNEL or REQ_CHANNEL) and not await is_subscribed(bot, query):
            await query.answer(
                results=[],
                cache_time=0,
                switch_pm_text='📢 Subscribe to use the bot',
                switch_pm_parameter="subscribe"
            )
            return

        # Parse query
        if '|' in query.query:
            string, file_type = query.query.split('|', maxsplit=1)
            string = string.strip()
            file_type = file_type.strip().lower()
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

            # Format caption
            if CUSTOM_FILE_CAPTION:
                try:
                    f_caption = CUSTOM_FILE_CAPTION.format(
                        file_name=title or '',
                        file_size=size or '',
                        file_caption=f_caption or ''
                    )
                except Exception as e:
                    logger.exception("Caption formatting error: %s", str(e))
                    f_caption = f_caption or title

            if not f_caption:
                f_caption = title

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
            if string:
                switch_pm_text += f" for {string}"
            switch_pm_param = "start"
        else:
            switch_pm_text = f'{emoji.CROSS_MARK} No results'
            if string:
                switch_pm_text += f' for "{string}"'
            switch_pm_param = "okay"

        # Send response
        await query.answer(
            results=results,
            is_personal=True,
            cache_time=cache_time,
            switch_pm_text=switch_pm_text,
            switch_pm_parameter=switch_pm_param,
            next_offset=str(next_offset) if results else None
        )

    except QueryIdInvalid:
        logger.warning("QueryIdInvalid: Inline query expired or reused.")
    except Exception as e:
        logger.exception("Unexpected error in inline query handler: %s", str(e))
        
