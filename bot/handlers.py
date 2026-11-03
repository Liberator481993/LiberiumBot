from __future__ import annotations

import asyncio
import html
import logging
from typing import Any

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.config import Settings
from bot.db import (
    delete_content,
    get_content,
    get_stats,
    get_user,
    list_user_ids,
    set_language,
    touch_user,
    upsert_content,
)
from bot.i18n import LANGUAGE_NAMES, tr
from bot.keyboards import (
    CATALOGS,
    admin_categories_keyboard,
    admin_items_keyboard,
    admin_keyboard,
    catalog_keyboard,
    channel_post_confirmation_keyboard,
    channel_post_style_keyboard,
    download_keyboard,
    language_keyboard,
    main_keyboard,
    subscription_keyboard,
)

router = Router(name="liberium")
log = logging.getLogger(__name__)

MM2_LOADSTRING = 'loadstring(game:HttpGet("https://raw.githubusercontent.com/Liberator481993/MM2HUB/refs/heads/main/MM2HUB"))()'


class ContentWizard(StatesGroup):
    title_ru = State()
    title_en = State()
    body_ru = State()
    body_en = State()
    version = State()
    url = State()
    file = State()
    image = State()


class BroadcastWizard(StatesGroup):
    message = State()


class ChannelPostWizard(StatesGroup):
    text = State()
    photo = State()
    button = State()
    style = State()
    confirm = State()


def _language(user: dict[str, Any] | None) -> str:
    value = (user or {}).get("language") or "ru"
    return value if value in {"ru", "en"} else "ru"


def _is_admin(user_id: int, settings: Settings) -> bool:
    return user_id in settings.admin_ids


async def _user_context(message: Message, settings: Settings) -> dict[str, Any]:
    await touch_user(
        settings.database_path,
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )
    return await get_user(settings.database_path, message.from_user.id) or {}


async def _callback_user_context(
    callback: CallbackQuery, settings: Settings
) -> dict[str, Any]:
    await touch_user(
        settings.database_path,
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name,
    )
    return await get_user(settings.database_path, callback.from_user.id) or {}


async def _is_subscribed(bot: Bot, user_id: int, settings: Settings) -> bool:
    try:
        member = await bot.get_chat_member(
            chat_id=settings.channel_id,
            user_id=user_id,
        )
        return member.status in {"member", "administrator", "creator"}
    except (TelegramBadRequest, TelegramForbiddenError):
        log.exception(
            "Could not verify channel membership. Check CHANNEL_ID and bot admin rights."
        )
        return False


async def _show_subscription(
    message: Message, language: str, settings: Settings
) -> None:
    await message.answer(
        tr(language, "subscribe_required"),
        reply_markup=subscription_keyboard(language, settings.channel_url),
    )


async def _check_message_access(
    message: Message, bot: Bot, settings: Settings, language: str
) -> bool:
    if await _is_subscribed(bot, message.from_user.id, settings):
        return True
    await _show_subscription(message, language, settings)
    return False


async def _check_callback_access(
    callback: CallbackQuery, bot: Bot, settings: Settings, language: str
) -> bool:
    if await _is_subscribed(bot, callback.from_user.id, settings):
        return True
    await callback.answer(tr(language, "not_subscribed"), show_alert=True)
    if callback.message:
        await _show_subscription(callback.message, language, settings)
    return False


async def _show_home(
    message: Message, language: str, settings: Settings, user_id: int
) -> None:
    await message.answer(
        tr(language, "welcome"),
        reply_markup=main_keyboard(language, _is_admin(user_id, settings)),
    )


@router.message(CommandStart())
async def start(message: Message, bot: Bot, settings: Settings) -> None:
    user = await _user_context(message, settings)
    language = _language(user)

    if not user.get("language"):
        await message.answer(
            tr("ru", "choose_language"),
            reply_markup=language_keyboard(),
        )
        return

    if not await _check_message_access(message, bot, settings, language):
        return
    await _show_home(message, language, settings, message.from_user.id)


@router.callback_query(F.data.startswith("lang:"))
async def choose_language(
    callback: CallbackQuery, bot: Bot, settings: Settings
) -> None:
    language = callback.data.split(":", 1)[1]
    if language not in {"ru", "en"}:
        await callback.answer("Unknown language", show_alert=True)
        return

    await _callback_user_context(callback, settings)
    await set_language(settings.database_path, callback.from_user.id, language)
    await callback.answer(tr(language, "language_changed"))

    if not await _check_callback_access(callback, bot, settings, language):
        return
    if callback.message:
        await callback.message.answer(
            tr(language, "language_saved") + "\n\n" + tr(language, "welcome"),
            reply_markup=main_keyboard(
                language, _is_admin(callback.from_user.id, settings)
            ),
        )


@router.callback_query(F.data == "sub:check")
async def check_subscription(
    callback: CallbackQuery, bot: Bot, settings: Settings
) -> None:
    user = await _callback_user_context(callback, settings)
    language = _language(user)
    if not await _is_subscribed(bot, callback.from_user.id, settings):
        await callback.answer(tr(language, "not_subscribed"), show_alert=True)
        return

    await callback.answer(tr(language, "subscribed"))
    if callback.message:
        await callback.message.answer(
            tr(language, "welcome"),
            reply_markup=main_keyboard(
                language, _is_admin(callback.from_user.id, settings)
            ),
        )


@router.message(Command("language"))
async def language_command(message: Message, settings: Settings) -> None:
    user = await _user_context(message, settings)
    language = _language(user)
    await message.answer(
        tr(language, "choose_language"),
        reply_markup=language_keyboard(),
    )


@router.message(Command("help"))
async def help_command(message: Message, settings: Settings) -> None:
    user = await _user_context(message, settings)
    language = _language(user)
    await message.answer(tr(language, "support"))


@router.message(Command("cancel"))
async def cancel_action(message: Message, state: FSMContext, settings: Settings) -> None:
    user = await _user_context(message, settings)
    language = _language(user)
    await state.clear()
    await message.answer(tr(language, "cancelled"))


async def _open_catalog(
    message: Message,
    category: str,
    bot: Bot,
    settings: Settings,
    language: str,
) -> None:
    if not await _check_message_access(message, bot, settings, language):
        return
    if category not in CATALOGS:
        return
    await message.answer(
        tr(language, "choose_item"),
        reply_markup=catalog_keyboard(category, language),
    )


@router.message(F.text.in_({"🎮 Скрипты", "🎮 Scripts"}))
async def scripts_menu(message: Message, bot: Bot, settings: Settings) -> None:
    user = await _user_context(message, settings)
    await _open_catalog(message, "scripts", bot, settings, _language(user))


@router.message(F.text.in_({"📲 Инжекторы", "📲 Injectors"}))
async def injectors_menu(message: Message, bot: Bot, settings: Settings) -> None:
    user = await _user_context(message, settings)
    await _open_catalog(message, "injectors", bot, settings, _language(user))


@router.message(F.text.in_({"📚 Гайды", "📚 Guides"}))
async def guides_menu(message: Message, bot: Bot, settings: Settings) -> None:
    user = await _user_context(message, settings)
    await _open_catalog(message, "guides", bot, settings, _language(user))


@router.message(F.text.in_({"👤 Профиль", "👤 Profile"}))
async def profile_menu(message: Message, bot: Bot, settings: Settings) -> None:
    user = await _user_context(message, settings)
    language = _language(user)
    if not await _check_message_access(message, bot, settings, language):
        return
    await message.answer(
        tr(
            language,
            "profile_text",
            user_id=message.from_user.id,
            language=LANGUAGE_NAMES.get(language, language),
        )
    )


@router.message(F.text.in_({"🌐 Язык", "🌐 Language"}))
async def language_menu(message: Message, settings: Settings) -> None:
    user = await _user_context(message, settings)
    language = _language(user)
    await message.answer(
        tr(language, "choose_language"),
        reply_markup=language_keyboard(),
    )


@router.callback_query(F.data == "nav:home")
async def back_home(
    callback: CallbackQuery, settings: Settings
) -> None:
    user = await _callback_user_context(callback, settings)
    language = _language(user)
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            tr(language, "welcome"),
            reply_markup=main_keyboard(
                language, _is_admin(callback.from_user.id, settings)
            ),
        )


async def _send_text_file_as_code(message: Message, bot: Bot, file_id: str) -> bool:
    """Send a stored text script as Telegram code blocks with copy controls."""
    try:
        downloaded = await bot.download(file_id)
        if downloaded is None:
            return False
        raw = downloaded.getvalue()
        script = raw.decode("utf-8-sig")
    except (UnicodeDecodeError, OSError, TelegramBadRequest, TelegramForbiddenError):
        return False

    # Telegram messages are limited to 4096 characters. Keep room for HTML tags.
    max_chunk = 3800
    while script:
        if len(script) <= max_chunk:
            chunk, script = script, ""
        else:
            split_at = script.rfind("\\n", 0, max_chunk)
            if split_at <= 0:
                split_at = max_chunk
            else:
                split_at += 1
            chunk, script = script[:split_at], script[split_at:]
        await message.answer(
            f"<pre><code>{html.escape(chunk)}</code></pre>",
            parse_mode="HTML",
        )
    return True


@router.callback_query(F.data.startswith("item:"))
async def open_catalog_item(
    callback: CallbackQuery, bot: Bot, settings: Settings
) -> None:
    user = await _callback_user_context(callback, settings)
    language = _language(user)
    if not await _check_callback_access(callback, bot, settings, language):
        return

    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer()
        return
    _, category, slug = parts
    if category not in CATALOGS or slug not in {item[0] for item in CATALOGS[category]}:
        await callback.answer("Unknown item", show_alert=True)
        return

    await callback.answer()
    if not callback.message:
        return

    # MM2 is served directly from the bot source and does not require
    # an admin-published SQLite catalog entry.
    if category == "scripts" and slug == "mm2":
        title = "Murder Mystery 2" if language == "en" else "Murder Mystery 2"
        await callback.message.answer(
            f"<b>{title}</b>\\n\\n"
            + ("Tap the code to copy the script:" if language == "en" else "Нажми на код, чтобы скопировать скрипт:")
            + f"\\n\\n<pre><code>{html.escape(MM2_LOADSTRING)}</code></pre>",
            parse_mode="HTML",
        )
        return

    item = await get_content(settings.database_path, category, slug)
    if not item:
        await callback.message.answer(tr(language, "not_published"))
        return

    title_key = "title_ru" if language == "ru" else "title_en"
    body_key = "body_ru" if language == "ru" else "body_en"
    title = html.escape(item[title_key] or "")
    body = html.escape(item[body_key] or "")
    version = html.escape(item["version"] or "")
    text = f"<b>{title}</b>"
    if version:
        text += f"\n{tr(language, 'version')}: <code>{version}</code>"
    if body:
        text += f"\n\n{body}"

    markup = download_keyboard(language, item["url"])
    if item.get("image_file_id"):
        await callback.message.answer_photo(
            photo=item["image_file_id"],
            caption=text,
            reply_markup=markup,
        )
    else:
        await callback.message.answer(text, reply_markup=markup)
    # MM2 script is maintained directly in the bot source; no admin TXT upload is needed.
    if category == "scripts" and slug == "mm2":
        await callback.message.answer(
            f"<pre><code>{html.escape(MM2_LOADSTRING)}</code></pre>",
            parse_mode="HTML",
        )
    elif item["file_id"]:
        file_name = item["file_name"] or "download"
        suffix = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
        text_extensions = {"txt", "lua", "luau", "py", "js", "json", "xml", "md"}
        sent_as_code = False
        if suffix in text_extensions:
            sent_as_code = await _send_text_file_as_code(
                callback.message, bot, item["file_id"]
            )
        if not sent_as_code:
            try:
                await callback.message.answer_document(
                    document=item["file_id"],
                    caption=html.escape(file_name),
                )
            except (TelegramBadRequest, TelegramForbiddenError):
                log.exception("Failed to send stored content file: %s/%s", category, slug)


@router.message(Command("admin"))
async def admin_command(
    message: Message, settings: Settings, state: FSMContext, bot: Bot
) -> None:
    user = await _user_context(message, settings)
    language = _language(user)
    if not _is_admin(message.from_user.id, settings):
        await message.answer(tr(language, "admin_denied"))
        return
    if not await _check_message_access(message, bot, settings, language):
        return
    await state.clear()
    await message.answer(
        tr(language, "admin_title"),
        reply_markup=admin_keyboard(language),
    )


@router.message(F.text.in_({"🛠 Админ-панель", "🛠 Admin panel"}))
async def admin_menu_button(
    message: Message, settings: Settings, state: FSMContext, bot: Bot
) -> None:
    user = await _user_context(message, settings)
    language = _language(user)
    if not _is_admin(message.from_user.id, settings):
        await message.answer(tr(language, "admin_denied"))
        return
    if not await _check_message_access(message, bot, settings, language):
        return
    await state.clear()
    await message.answer(
        tr(language, "admin_title"),
        reply_markup=admin_keyboard(language),
    )


async def _admin_callback_guard(
    callback: CallbackQuery, bot: Bot, settings: Settings
) -> tuple[bool, str]:
    user = await _callback_user_context(callback, settings)
    language = _language(user)
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer(tr(language, "admin_denied"), show_alert=True)
        return False, language
    if not await _check_callback_access(callback, bot, settings, language):
        return False, language
    return True, language


@router.callback_query(F.data == "adm:home")
async def admin_home(
    callback: CallbackQuery, bot: Bot, settings: Settings
) -> None:
    allowed, language = await _admin_callback_guard(callback, bot, settings)
    if not allowed:
        return
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            tr(language, "admin_title"), reply_markup=admin_keyboard(language)
        )


@router.callback_query(F.data == "adm:content")
async def admin_content(
    callback: CallbackQuery, bot: Bot, settings: Settings
) -> None:
    allowed, language = await _admin_callback_guard(callback, bot, settings)
    if not allowed:
        return
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            tr(language, "admin_choose_category"),
            reply_markup=admin_categories_keyboard(language),
        )


@router.callback_query(F.data.startswith("adm:category:"))
async def admin_category_items(
    callback: CallbackQuery, bot: Bot, settings: Settings
) -> None:
    allowed, language = await _admin_callback_guard(callback, bot, settings)
    if not allowed:
        return
    category = callback.data.rsplit(":", 1)[-1]
    if category not in CATALOGS:
        await callback.answer("Unknown section", show_alert=True)
        return
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            tr(language, "admin_choose_item"),
            reply_markup=admin_items_keyboard(category, language),
        )


@router.callback_query(F.data.startswith("adm:edit:"))
async def admin_edit_item(
    callback: CallbackQuery,
    bot: Bot,
    settings: Settings,
    state: FSMContext,
) -> None:
    allowed, language = await _admin_callback_guard(callback, bot, settings)
    if not allowed:
        return
    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer()
        return
    _, _, category, slug = parts
    if category not in CATALOGS or slug not in {item[0] for item in CATALOGS[category]}:
        await callback.answer("Unknown item", show_alert=True)
        return

    await state.clear()
    await state.update_data(category=category, slug=slug)
    await state.set_state(ContentWizard.title_ru)
    await callback.answer()
    if callback.message:
        await callback.message.answer(tr(language, "admin_title_ru"))


@router.callback_query(F.data.startswith("adm:delete:"))
async def admin_delete_item(
    callback: CallbackQuery, bot: Bot, settings: Settings
) -> None:
    allowed, language = await _admin_callback_guard(callback, bot, settings)
    if not allowed:
        return
    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer()
        return
    _, _, category, slug = parts
    if category not in CATALOGS or slug not in {item[0] for item in CATALOGS[category]}:
        await callback.answer("Unknown item", show_alert=True)
        return
    await delete_content(settings.database_path, category, slug)
    await callback.answer(tr(language, "admin_deleted"))
    if callback.message:
        await callback.message.answer(tr(language, "admin_deleted"))


@router.message(ContentWizard.title_ru)
async def wizard_title_ru(message: Message, state: FSMContext, settings: Settings) -> None:
    if not message.text or not message.text.strip():
        user = await get_user(settings.database_path, message.from_user.id)
        await message.answer(tr(_language(user), "admin_title_ru"))
        return
    await state.update_data(title_ru=message.text.strip())
    await state.set_state(ContentWizard.title_en)
    user = await get_user(settings.database_path, message.from_user.id)
    await message.answer(tr(_language(user), "admin_title_en"))


@router.message(ContentWizard.title_en)
async def wizard_title_en(message: Message, state: FSMContext, settings: Settings) -> None:
    if not message.text or not message.text.strip():
        await message.answer("Please send a text title.")
        return
    await state.update_data(title_en=message.text.strip())
    await state.set_state(ContentWizard.body_ru)
    user = await get_user(settings.database_path, message.from_user.id)
    await message.answer(tr(_language(user), "admin_body_ru"))


@router.message(ContentWizard.body_ru)
async def wizard_body_ru(message: Message, state: FSMContext, settings: Settings) -> None:
    if not message.text:
        await message.answer("Please send the description as text.")
        return
    await state.update_data(body_ru=message.text.strip())
    await state.set_state(ContentWizard.body_en)
    user = await get_user(settings.database_path, message.from_user.id)
    await message.answer(tr(_language(user), "admin_body_en"))


@router.message(ContentWizard.body_en)
async def wizard_body_en(message: Message, state: FSMContext, settings: Settings) -> None:
    if not message.text:
        await message.answer("Please send the description as text.")
        return
    await state.update_data(body_en=message.text.strip())
    await state.set_state(ContentWizard.version)
    user = await get_user(settings.database_path, message.from_user.id)
    await message.answer(tr(_language(user), "admin_version"))


@router.message(ContentWizard.version)
async def wizard_version(message: Message, state: FSMContext, settings: Settings) -> None:
    if not message.text:
        await message.answer("Please send a version or '-'.")
        return
    value = message.text.strip()
    await state.update_data(version="" if value == "-" else value)
    await state.set_state(ContentWizard.url)
    user = await get_user(settings.database_path, message.from_user.id)
    await message.answer(tr(_language(user), "admin_url"))


@router.message(ContentWizard.url)
async def wizard_url(message: Message, state: FSMContext, settings: Settings) -> None:
    if not message.text:
        user = await get_user(settings.database_path, message.from_user.id)
        await message.answer(tr(_language(user), "admin_invalid_url"))
        return
    value = message.text.strip()
    if value != "-" and not value.startswith(("https://", "http://")):
        user = await get_user(settings.database_path, message.from_user.id)
        await message.answer(tr(_language(user), "admin_invalid_url"))
        return
    await state.update_data(url="" if value == "-" else value)
    await state.set_state(ContentWizard.file)
    user = await get_user(settings.database_path, message.from_user.id)
    await message.answer(tr(_language(user), "admin_file"))


@router.message(ContentWizard.file)
async def wizard_file(
    message: Message, state: FSMContext, settings: Settings
) -> None:
    file_id = ""
    file_name = ""
    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name or "download"
    elif message.text and message.text.strip().lower() in {"/skip", "-"}:
        pass
    else:
        user = await get_user(settings.database_path, message.from_user.id)
        await message.answer(tr(_language(user), "admin_file_prompt"))
        return

    await state.update_data(file_id=file_id, file_name=file_name)
    await state.set_state(ContentWizard.image)
    user = await get_user(settings.database_path, message.from_user.id)
    await message.answer(tr(_language(user), "admin_image"))


@router.message(ContentWizard.image)
async def wizard_image(
    message: Message, state: FSMContext, settings: Settings
) -> None:
    image_file_id = ""
    if message.photo:
        image_file_id = message.photo[-1].file_id
    elif message.text and message.text.strip().lower() in {"/skip", "-"}:
        pass
    else:
        user = await get_user(settings.database_path, message.from_user.id)
        await message.answer(tr(_language(user), "admin_image_prompt"))
        return

    data = await state.get_data()
    await upsert_content(
        settings.database_path,
        category=data["category"],
        slug=data["slug"],
        title_ru=data["title_ru"],
        title_en=data["title_en"],
        body_ru=data["body_ru"],
        body_en=data["body_en"],
        version=data.get("version", ""),
        url=data.get("url", ""),
        file_id=data.get("file_id", ""),
        file_name=data.get("file_name", ""),
        image_file_id=image_file_id,
    )
    await state.clear()
    user = await get_user(settings.database_path, message.from_user.id)
    await message.answer(tr(_language(user), "admin_saved"))


@router.callback_query(F.data == "adm:broadcast")
async def admin_broadcast_start(
    callback: CallbackQuery,
    bot: Bot,
    settings: Settings,
    state: FSMContext,
) -> None:
    allowed, language = await _admin_callback_guard(callback, bot, settings)
    if not allowed:
        return
    await state.clear()
    await state.set_state(BroadcastWizard.message)
    await callback.answer()
    if callback.message:
        await callback.message.answer(tr(language, "admin_broadcast_prompt"))


@router.message(BroadcastWizard.message)
async def admin_broadcast_send(
    message: Message, bot: Bot, settings: Settings, state: FSMContext
) -> None:
    if message.from_user.id not in settings.admin_ids:
        await state.clear()
        return
    user = await get_user(settings.database_path, message.from_user.id)
    language = _language(user)
    recipients = await list_user_ids(settings.database_path)
    sent = 0
    failed = 0
    for user_id in recipients:
        try:
            await bot.copy_message(
                chat_id=user_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id,
            )
            sent += 1
        except (TelegramBadRequest, TelegramForbiddenError):
            failed += 1
        await asyncio.sleep(0.04)

    await state.clear()
    await message.answer(
        tr(language, "admin_broadcast_done", sent=sent, failed=failed)
    )



@router.callback_query(F.data == "adm:channel_post")
async def admin_channel_post_start(
    callback: CallbackQuery, bot: Bot, settings: Settings, state: FSMContext
) -> None:
    allowed, language = await _admin_callback_guard(callback, bot, settings)
    if not allowed:
        return
    await state.clear()
    await state.set_state(ChannelPostWizard.text)
    await callback.answer()
    if callback.message:
        await callback.message.answer(tr(language, "admin_post_text"))


@router.message(ChannelPostWizard.text)
async def channel_post_text(message: Message, state: FSMContext, settings: Settings) -> None:
    if message.from_user.id not in settings.admin_ids:
        await state.clear()
        return
    if not message.text or not message.text.strip():
        user = await get_user(settings.database_path, message.from_user.id)
        await message.answer(tr(_language(user), "admin_post_text"))
        return
    await state.update_data(post_text=message.text.strip())
    await state.set_state(ChannelPostWizard.photo)
    user = await get_user(settings.database_path, message.from_user.id)
    await message.answer(tr(_language(user), "admin_post_photo"))


@router.message(ChannelPostWizard.photo)
async def channel_post_photo(message: Message, state: FSMContext, settings: Settings) -> None:
    if message.from_user.id not in settings.admin_ids:
        await state.clear()
        return
    photo_id = ""
    if message.photo:
        photo_id = message.photo[-1].file_id
        data = await state.get_data()
        if len(data.get("post_text", "")) > 1024:
            user = await get_user(settings.database_path, message.from_user.id)
            await message.answer(tr(_language(user), "admin_post_caption_too_long"))
            return
    elif message.text and message.text.strip().lower() in {"/skip", "-"}:
        pass
    else:
        user = await get_user(settings.database_path, message.from_user.id)
        await message.answer(tr(_language(user), "admin_post_photo"))
        return
    await state.update_data(post_photo_id=photo_id)
    await state.set_state(ChannelPostWizard.button)
    user = await get_user(settings.database_path, message.from_user.id)
    await message.answer(tr(_language(user), "admin_post_button"))


@router.message(ChannelPostWizard.button)
async def channel_post_button(message: Message, state: FSMContext, settings: Settings) -> None:
    if message.from_user.id not in settings.admin_ids:
        await state.clear()
        return
    if not message.text or not message.text.strip() or len(message.text.strip()) > 64:
        user = await get_user(settings.database_path, message.from_user.id)
        await message.answer(tr(_language(user), "admin_post_button_invalid"))
        return
    await state.update_data(post_button_text=message.text.strip())
    await state.set_state(ChannelPostWizard.style)
    user = await get_user(settings.database_path, message.from_user.id)
    language = _language(user)
    await message.answer(
        tr(language, "admin_post_style"),
        reply_markup=channel_post_style_keyboard(language),
    )


@router.callback_query(F.data.startswith("adm:post:style:"))
async def channel_post_style(
    callback: CallbackQuery, bot: Bot, settings: Settings, state: FSMContext
) -> None:
    allowed, language = await _admin_callback_guard(callback, bot, settings)
    if not allowed:
        return
    style = callback.data.rsplit(":", 1)[-1]
    if style not in {"primary", "success", "danger"}:
        await callback.answer("Unknown button style", show_alert=True)
        return
    if await state.get_state() != ChannelPostWizard.style.state:
        await callback.answer(tr(language, "admin_post_expired"), show_alert=True)
        return

    await state.update_data(post_button_style=style)
    await state.set_state(ChannelPostWizard.confirm)
    data = await state.get_data()
    me = await bot.get_me()
    if not me.username:
        await callback.answer(tr(language, "admin_post_failed"), show_alert=True)
        return
    preview_markup = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=data["post_button_text"],
            url=f"https://t.me/{me.username}?start=home",
            style=style,
        )
    ]])
    await callback.answer()
    if callback.message:
        if data.get("post_photo_id"):
            await callback.message.answer_photo(
                photo=data["post_photo_id"], caption=data["post_text"],
                reply_markup=preview_markup, parse_mode=None
            )
        else:
            await callback.message.answer(
                data["post_text"], reply_markup=preview_markup, parse_mode=None
            )
        await callback.message.answer(
            tr(language, "admin_post_confirm"),
            reply_markup=channel_post_confirmation_keyboard(language),
        )


@router.callback_query(F.data == "adm:post:cancel")
async def channel_post_cancel(
    callback: CallbackQuery, bot: Bot, settings: Settings, state: FSMContext
) -> None:
    allowed, language = await _admin_callback_guard(callback, bot, settings)
    if not allowed:
        return
    await state.clear()
    await callback.answer()
    if callback.message:
        await callback.message.answer(tr(language, "cancelled"))


@router.callback_query(F.data == "adm:post:publish")
async def channel_post_publish(
    callback: CallbackQuery, bot: Bot, settings: Settings, state: FSMContext
) -> None:
    allowed, language = await _admin_callback_guard(callback, bot, settings)
    if not allowed:
        return
    if await state.get_state() != ChannelPostWizard.confirm.state:
        await callback.answer(tr(language, "admin_post_expired"), show_alert=True)
        return
    data = await state.get_data()
    try:
        me = await bot.get_me()
        if not me.username:
            raise RuntimeError("Bot username is unavailable")
        button_url = f"https://t.me/{me.username}?start=home"
        markup = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text=data["post_button_text"],
                url=button_url,
                style=data.get("post_button_style", "primary"),
            )
        ]])
        if data.get("post_photo_id"):
            await bot.send_photo(
                chat_id=settings.channel_id, photo=data["post_photo_id"],
                caption=data["post_text"], reply_markup=markup, parse_mode=None
            )
        else:
            await bot.send_message(
                chat_id=settings.channel_id, text=data["post_text"],
                reply_markup=markup, parse_mode=None
            )
    except (TelegramBadRequest, TelegramForbiddenError, RuntimeError):
        log.exception("Failed to publish channel post; check channel ID and bot admin rights.")
        await callback.answer(tr(language, "admin_post_failed"), show_alert=True)
        return
    await state.clear()
    await callback.answer(tr(language, "admin_post_published"))
    if callback.message:
        await callback.message.answer(tr(language, "admin_post_published"))


@router.callback_query(F.data == "adm:stats")
async def admin_statistics(
    callback: CallbackQuery, bot: Bot, settings: Settings
) -> None:
    allowed, language = await _admin_callback_guard(callback, bot, settings)
    if not allowed:
        return
    stats = await get_stats(settings.database_path)
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            tr(
                language,
                "admin_stats",
                users=stats["users"],
                content=stats["content"],
            )
        )


@router.message()
async def fallback_message(message: Message, settings: Settings) -> None:
    if not message.from_user:
        return
    user = await _user_context(message, settings)
    language = _language(user)
    await message.answer(
        tr(language, "choose_section"),
        reply_markup=main_keyboard(
            language, _is_admin(message.from_user.id, settings)
        ),
    )
