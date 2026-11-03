from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from bot.i18n import main_menu_labels, tr


CATALOGS = {
    "scripts": [
        ("mm2", "Murder Mystery 2"),
        ("adopt_me", "Adopt Me"),
        ("blade_ball", "Blade Ball"),
    ],
    "injectors": [
        ("delta", "Delta"),
        ("arceus_x", "Arceus X"),
    ],
    "guides": [
        ("install", "Установка / Installation"),
        ("launch", "Запуск / Launch"),
        ("troubleshooting", "Решение проблем / Troubleshooting"),
    ],
}


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
        ]]
    )


def subscription_keyboard(language: str, channel_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=tr(language, "subscribe_button"), url=channel_url
            )],
            [InlineKeyboardButton(
                text=tr(language, "check_button"), callback_data="sub:check"
            )],
        ]
    )


def main_keyboard(language: str, is_admin: bool) -> ReplyKeyboardMarkup:
    labels = main_menu_labels(language)
    rows = [
        [KeyboardButton(text=labels["scripts"]), KeyboardButton(text=labels["injectors"])],
        [KeyboardButton(text=labels["guides"]), KeyboardButton(text=labels["profile"])],
        [KeyboardButton(text=labels["language"])],
    ]
    if is_admin:
        rows.append([KeyboardButton(text=labels["admin"])])
    return ReplyKeyboardMarkup(
        keyboard=rows, resize_keyboard=True, input_field_placeholder=tr(language, "choose_section")
    )


def catalog_keyboard(category: str, language: str) -> InlineKeyboardMarkup:
    rows = []
    for slug, title in CATALOGS[category]:
        rows.append([InlineKeyboardButton(
            text=title, callback_data=f"item:{category}:{slug}"
        )])
    rows.append([InlineKeyboardButton(
        text=tr(language, "back"), callback_data="nav:home"
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=tr(language, "admin_menu_content"), callback_data="adm:content"
        )],
        [InlineKeyboardButton(
            text=tr(language, "admin_menu_broadcast"), callback_data="adm:broadcast"
        )],
        [InlineKeyboardButton(
            text=tr(language, "admin_menu_stats"), callback_data="adm:stats"
        )],
        [InlineKeyboardButton(
            text=tr(language, "back"), callback_data="nav:home"
        )],
    ])


def admin_categories_keyboard(language: str) -> InlineKeyboardMarkup:
    labels = {
        "scripts": tr(language, "scripts"),
        "injectors": tr(language, "injectors"),
        "guides": tr(language, "guides"),
    }
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, callback_data=f"adm:category:{key}")]
        for key, label in labels.items()
    ] + [[InlineKeyboardButton(
        text=tr(language, "back"), callback_data="adm:home"
    )]])


def admin_items_keyboard(category: str, language: str) -> InlineKeyboardMarkup:
    rows = []
    for slug, title in CATALOGS[category]:
        rows.append([
            InlineKeyboardButton(text=title, callback_data=f"adm:edit:{category}:{slug}"),
            InlineKeyboardButton(text=tr(language, "admin_delete"), callback_data=f"adm:delete:{category}:{slug}"),
        ])
    rows.append([InlineKeyboardButton(
        text=tr(language, "back"), callback_data="adm:content"
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def download_keyboard(language: str, url: str) -> InlineKeyboardMarkup | None:
    if not url:
        return None
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(language, "download"), url=url)
    ]])
