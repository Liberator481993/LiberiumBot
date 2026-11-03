from __future__ import annotations

TEXTS = {
    "ru": {
        "choose_language": "🌐 Выбери язык интерфейса:",
        "language_saved": "Язык сохранён: Русский 🇷🇺",
        "welcome": (
            "✨ <b>Добро пожаловать в Liberium Bot!</b>\n\n"
            "Здесь собраны скрипты, инжекторы и полезные инструкции "
            "экосистемы Liberium."
        ),
        "subscribe_required": (
            "🔒 <b>Для доступа к боту нужна подписка на канал.</b>\n"
            "Подпишись и нажми «Проверить подписку»."
        ),
        "subscribe_button": "📢 Открыть канал",
        "check_button": "✅ Проверить подписку",
        "not_subscribed": "Подписка пока не найдена. Сначала подпишись на канал.",
        "subscribed": "✅ Подписка подтверждена!",
        "scripts": "🎮 Скрипты",
        "injectors": "📲 Инжекторы",
        "guides": "📚 Гайды",
        "profile": "👤 Профиль",
        "language": "🌐 Язык",
        "admin": "🛠 Админ-панель",
        "choose_section": "Выбери раздел:",
        "choose_item": "Выбери нужный материал:",
        "not_published": "Этот материал пока не опубликован. Загляни позже.",
        "version": "Версия",
        "download": "📥 Скачать / открыть",
        "back": "⬅️ Назад",
        "profile_text": (
            "👤 <b>Твой профиль</b>\n"
            "ID: <code>{user_id}</code>\n"
            "Язык: {language}"
        ),
        "language_changed": "Язык интерфейса обновлён.",
        "admin_denied": "⛔ У тебя нет доступа к админ-панели.",
        "admin_title": "🛠 <b>Панель управления Liberium</b>",
        "admin_menu_content": "🗂 Управление материалами",
        "admin_menu_broadcast": "📣 Рассылка",
        "admin_menu_stats": "📊 Статистика",
        "admin_menu_channel_post": "📢 Создать пост в канал",
        "admin_post_text": "Отправь текст поста для канала:",
        "admin_post_photo": "Отправь фото к посту или /skip, если пост будет только текстовым:",
        "admin_post_caption_too_long": "Подпись к фото должна быть не длиннее 1024 символов. Сократи текст и отправь фото снова.",
        "admin_post_button": "Напиши свой текст для кнопки под постом (до 64 символов):",
        "admin_post_button_invalid": "Текст кнопки должен содержать от 1 до 64 символов. Отправь его ещё раз:",
        "admin_post_style": "Теперь выбери цвет кнопки под постом:",
        "admin_post_style_blue": "🔵 Синий",
        "admin_post_style_green": "🟢 Зелёный",
        "admin_post_style_red": "🔴 Красный",
        "admin_post_confirm": "Проверь пост выше. Опубликовать его в канал?",
        "admin_post_publish_button": "🚀 Опубликовать",
        "admin_post_cancel_button": "✖️ Отмена",
        "admin_post_published": "✅ Пост опубликован в канале.",
        "admin_post_failed": "Не удалось опубликовать пост. Проверь, что бот добавлен в канал администратором с правом публикации.",
        "admin_post_expired": "Черновик не найден или уже завершён. Создай пост заново.",
        "admin_choose_category": "Выбери раздел для управления:",
        "admin_choose_item": "Выбери материал. Его можно обновить или удалить:",
        "admin_edit": "✏️ Добавить / обновить",
        "admin_delete": "🗑 Удалить",
        "admin_deleted": "Материал удалён.",
        "admin_missing": "Такого материала ещё нет.",
        "admin_title_ru": "Отправь название на русском:",
        "admin_title_en": "Отправь название на английском:",
        "admin_body_ru": "Отправь описание на русском. Можно несколькими строками:",
        "admin_body_en": "Отправь описание на английском:",
        "admin_version": "Укажи версию или отправь «-», если версии нет:",
        "admin_url": "Отправь ссылку (https://...) или «-», если ссылки нет:",
        "admin_file": (
            "Теперь отправь файл (например, .txt или APK) как документ. "
            "Либо отправь /skip, чтобы пропустить."
        ),
        "admin_saved": "✅ Материал успешно сохранён.",
        "admin_invalid_url": "Нужна ссылка, начинающаяся с https:// или http://, либо «-».",
        "admin_file_prompt": "Отправь документ или /skip.",
        "admin_image": "Теперь отправь картинку для карточки материала как фото. Если без картинки — отправь /skip.",
        "admin_image_prompt": "Отправь изображение как фото или /skip.",
        "admin_broadcast_prompt": "Отправь сообщение для рассылки. Можно текст, фото или документ.",
        "admin_broadcast_done": "Рассылка завершена. Доставлено: {sent}, ошибок: {failed}.",
        "admin_stats": "📊 <b>Статистика</b>\nПользователей: {users}\nМатериалов: {content}",
        "cancelled": "Действие отменено.",
        "support": "По вопросам и предложениям напиши администрации канала @mm2hubscripts.",
    },
    "en": {
        "choose_language": "🌐 Choose your interface language:",
        "language_saved": "Language saved: English 🇬🇧",
        "welcome": (
            "✨ <b>Welcome to Liberium Bot!</b>\n\n"
            "Find scripts, injectors and useful guides from the Liberium ecosystem."
        ),
        "subscribe_required": (
            "🔒 <b>Channel subscription is required.</b>\n"
            "Subscribe to the channel, then tap “Check subscription”."
        ),
        "subscribe_button": "📢 Open channel",
        "check_button": "✅ Check subscription",
        "not_subscribed": "Subscription not found. Please join the channel first.",
        "subscribed": "✅ Subscription confirmed!",
        "scripts": "🎮 Scripts",
        "injectors": "📲 Injectors",
        "guides": "📚 Guides",
        "profile": "👤 Profile",
        "language": "🌐 Language",
        "admin": "🛠 Admin panel",
        "choose_section": "Choose a section:",
        "choose_item": "Choose an item:",
        "not_published": "This item has not been published yet. Check back later.",
        "version": "Version",
        "download": "📥 Download / open",
        "back": "⬅️ Back",
        "profile_text": (
            "👤 <b>Your profile</b>\n"
            "ID: <code>{user_id}</code>\n"
            "Language: {language}"
        ),
        "language_changed": "Interface language updated.",
        "admin_denied": "⛔ You do not have access to the admin panel.",
        "admin_title": "🛠 <b>Liberium control panel</b>",
        "admin_menu_content": "🗂 Manage content",
        "admin_menu_broadcast": "📣 Broadcast",
        "admin_menu_stats": "📊 Statistics",
        "admin_menu_channel_post": "📢 Create channel post",
        "admin_post_text": "Send the channel post text:",
        "admin_post_photo": "Send a photo for the post, or /skip for a text-only post:",
        "admin_post_caption_too_long": "A photo caption must be 1024 characters or fewer. Shorten the text and send the photo again.",
        "admin_post_button": "Enter your custom button label (up to 64 characters):",
        "admin_post_button_invalid": "The button label must contain 1–64 characters. Send it again:",
        "admin_post_style": "Now choose the color of the post button:",
        "admin_post_style_blue": "🔵 Blue",
        "admin_post_style_green": "🟢 Green",
        "admin_post_style_red": "🔴 Red",
        "admin_post_confirm": "Review the post above. Publish it to the channel?",
        "admin_post_publish_button": "🚀 Publish",
        "admin_post_cancel_button": "✖️ Cancel",
        "admin_post_published": "✅ The post has been published to the channel.",
        "admin_post_failed": "Could not publish the post. Make sure the bot is a channel administrator with permission to post messages.",
        "admin_post_expired": "The draft was not found or has already finished. Create the post again.",
        "admin_choose_category": "Choose a section to manage:",
        "admin_choose_item": "Choose an item to update or delete:",
        "admin_edit": "✏️ Add / update",
        "admin_delete": "🗑 Delete",
        "admin_deleted": "Content deleted.",
        "admin_missing": "This item does not exist yet.",
        "admin_title_ru": "Send the Russian title:",
        "admin_title_en": "Send the English title:",
        "admin_body_ru": "Send the Russian description:",
        "admin_body_en": "Send the English description:",
        "admin_version": "Send the version, or “-” if not applicable:",
        "admin_url": "Send a URL (https://...) or “-” if there is no link:",
        "admin_file": (
            "Now send a file (for example, .txt or APK) as a document, "
            "or send /skip to skip."
        ),
        "admin_saved": "✅ Content saved successfully.",
        "admin_invalid_url": "Send a URL starting with https:// or http://, or “-”.",
        "admin_file_prompt": "Send a document or /skip.",
        "admin_image": "Now send a picture for this item as a photo. Send /skip to continue without one.",
        "admin_image_prompt": "Send an image as a photo or /skip.",
        "admin_broadcast_prompt": "Send the message to broadcast. Text, photo or document are supported.",
        "admin_broadcast_done": "Broadcast finished. Delivered: {sent}, failed: {failed}.",
        "admin_stats": "📊 <b>Statistics</b>\nUsers: {users}\nContent items: {content}",
        "cancelled": "Action cancelled.",
        "support": "For help and suggestions, contact the channel administration: @mm2hubscripts.",
    },
}

LANGUAGE_NAMES = {"ru": "Русский 🇷🇺", "en": "English 🇬🇧"}


def tr(language: str, key: str, **kwargs: object) -> str:
    lang = language if language in TEXTS else "ru"
    return TEXTS[lang][key].format(**kwargs)


def main_menu_labels(language: str) -> dict[str, str]:
    return {key: tr(language, key) for key in (
        "scripts", "injectors", "guides", "profile", "language", "admin"
    )}
