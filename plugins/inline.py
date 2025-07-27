import logging
from pyrogram import Client, filters, emoji
from pyrogram.errors.exceptions.bad_request_400 import QueryIdInvalid
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultCachedDocument, InlineQuery
from database.ia_filterdb import get_search_results
from utils import is_subscribed, get_size, temp, check_verification
from info import CACHE_TIME, AUTH_USERS, AUTH_CHANNEL, CUSTOM_FILE_CAPTION, PREMIUM_MODE

logger = logging.getLogger(__name__)
cache_time = 0 if AUTH_USERS or AUTH_CHANNEL else CACHE_TIME


async def inline_users(query: InlineQuery):
    user_id = query.from_user.id if query.from_user else None

    if user_id is None:
        return False

    if AUTH_USERS:
        return user_id in AUTH_USERS

    return user_id not in temp.BANNED_USERS


@Client.on_inline_query()
async def answer(bot, query: InlineQuery):
    user_id = query.from_user.id

    # ✅ Step 1: Check if user is banned
    if not await inline_users(query):
        await query.answer(
            results=[],
            cache_time=0,
            switch_pm_text="⚠️ You are not allowed to use this bot.",
            switch_pm_parameter="not_allowed"
        )
        return

    # ✅ Step 2: Check subscription
    if AUTH_CHANNEL and not await is_subscribed(bot, query):
        await query.answer(
            results=[],
            cache_time=0,
            switch_pm_text='📢 Join our channel to use this bot.',
            switch_pm_parameter="subscribe"
        )
        return

    # ✅ Step 3: Premium Mode check
    if PREMIUM_MODE and not await check_verification(bot, message.from_user.id):
        await query.answer(
            results=[],
            cache_time=0,
            switch_pm_text="💎 Premium Only - ₹99\nTap to Buy Premium",
            switch_pm_parameter="premium"
        )
        return

    # ✅ Continue to search
    results = []

    if '|' in query.query:
        string, file_type = query.query.split('|', maxsplit=1)
        string = string.strip()
        file_type = file_type.strip().lower()
    else:
        string = query.query.strip()
        file_type = None

    offset = int(query.offset or 0)
    reply_markup = get_reply_markup(query=string)

    files, next_offset, total = await get_search_results(string, file_type=file_type, max_results=10, offset=offset)

    for file in files:
        title = file.file_name
        size = get_size(file.file_size)
        f_caption = file.caption

        # ✅ Custom caption logic
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(
                    mention=query.from_user.mention,
                    file_name=title or '',
                    file_size=size or '',
                    file_caption=f_caption or ''
                )
            except Exception as e:
                logger.exception("Custom caption error")
                f_caption = f_caption or title

        if f_caption is None:
            f_caption = f"{file.file_name}"

        results.append(
            InlineQueryResultCachedDocument(
                title=title,
                document_file_id=file.file_id,
                caption=f_caption,
                description=f'Size: {size}\nType: {file.file_type}',
                reply_markup=reply_markup
            )
        )

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
            logger.exception("Inline answer error")
    else:
        switch_pm_text = f'{emoji.CROSS_MARK} No Results'
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
    buttons = [[InlineKeyboardButton('⟳ 𝗦𝗲𝗮𝗿𝗰𝗵 𝗔𝗴𝗮𝗶𝗻', switch_inline_query_current_chat=query)]]
    return InlineKeyboardMarkup(buttons)
