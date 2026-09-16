# -*- coding: utf-8 -*-
"""
Telegram-бот для компании стройматериалов (Киев).
Дерево категорий -> подкатегории -> контакт менеджера.
Раздел доставки: под-меню по направлениям -> фото таблицы тарифов.
Библиотека: aiogram 3.x
"""

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile,
)

# ==========================================================================
# НАСТРОЙКИ — всё, что нужно менять, лежит здесь.
# ==========================================================================

# Токен бота от @BotFather. На Railway задаётся в Variables как BOT_TOKEN.
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Номер менеджера для звонка
MANAGER_PHONE = "+380670080788"

# ВПИШИ СЮДА реальный юзернейм менеджера в Телеграме (без @).
# Например, если у менеджера @ivan_sales — впиши "ivan_sales".
MANAGER_TELEGRAM = "kirill_budmaterialy"

# Приветствие (баннер-картинку добавим позже)
WELCOME_TEXT = (
    "👋 <b>Вітаємо!</b>\n\n"
    "Ми — компанія будівельних матеріалів у Києві.\n"
    "Оберіть категорію, і ми швидко з'єднаємо вас з менеджером.\n\n"
    "📍 <b>Наші склади в м. Київ:</b>\n"
    "• Склад №1 — пр-т Перемоги, 67, корпус Nb (м. Нивки)\n"
    "• Склад №2 — вул. Марка Вовчка, 14 (Куренівка)\n"
    "• Склад №3 — пров. Деревообробний, 5 (Видубичі)\n"
    "• Склад №4 — вул. Бориспільська, 7\n\n"
    "🕘 <b>Графік роботи складів:</b>\n"
    "Пн–Пт: 9:00–18:00 | Сб: 9:00–14:00 | Нд: вихідний\n\n"
    "📞 <b>Прийом замовлень:</b> Пн–Нд, 9:00–21:00"
)

# --------------------------------------------------------------------------
# ДЕРЕВО КАТЕГОРИЙ.
# --------------------------------------------------------------------------
CATEGORIES = {
    "facade": {
        "title": "🏠 Все для фасаду / Фасадні роботи",
        "subs": [
            "Приклейка та армування",
            "Вата та пінопласт",
            "Ґрунт та декоративні матеріали",
        ],
    },
    "plaster": {
        "title": "🧱 Все для штукатурки / Штукатурні роботи",
        "subs": [
            "Гіпсові штукатурки",
            "Цементні та цементно-вапняні штукатурки",
            "Розхідні матеріали для штукатурки",
        ],
    },
    "drywall": {
        "title": "▦ Все для гіпсокартону / Гіпсокартонні роботи",
        "subs": [
            "Гіпсокартон",
            "Профіль для гіпсокартону",
            "З'єднувальні та монтажні елементи",
        ],
    },
    "paint": {
        "title": "🎨 Все для малярних робіт / Малярні роботи",
        "subs": [
            "Шпаклівки",
            "Склохолст",
            "Клей для склохолста",
        ],
    },
    "screed": {
        "title": "🔩 Все для стяжки / Стяжка",
        "subs": [
            "Стяжка",
            'Сітка кладочна "Армопояс"',
            "Розхідні матеріали",
        ],
    },
    "tools": {
        "title": "🔧 Інструменти та розхідні матеріали",
        "subs": [
            "Індивідуальний захист",
            "Плівки",
            "Інструменти",
        ],
    },
    "delivery": {
        "title": "🚚 Тарифи на доставку",
        "subs": [],   # особый раздел — обрабатывается отдельно (под-меню направлений)
    },
}

# --------------------------------------------------------------------------
# НАПРАВЛЕНИЯ ДОСТАВКИ.
# "код": {"title": "текст кнопки", "file": "имя файла в папке images"}
#
# Имена файлов должны ТОЧНО совпадать с файлами в папке images на GitHub.
# Рекомендуется латиница без пробелов. Если файлы .png — поменяй .jpg на .png.
# --------------------------------------------------------------------------
DELIVERY_ZONES = {
    "kyiv": {
        "title": "🏙 Київ (базові тарифи)",
        "file": "kyiv.jpg",
    },
    "odesa_boryspil": {
        "title": "Одеське та Бориспільське",
        "file": "odesa_boryspil.jpg",
    },
    "obuhiv_brovary": {
        "title": "Обухівське та Броварське",
        "file": "obuhiv_brovary.jpg",
    },
    "borodyanka_byshiv": {
        "title": "Бородянське та Бишівське",
        "file": "borodyanka_byshiv.jpg",
    },
    "vyshgorod_zhytomyr": {
        "title": "Вишгородське, Вишневське, Житомирське",
        "file": "vyshgorod_zhytomyr.jpg",
    },
}

# Папка с картинками (лежит рядом с bot.py)
IMAGES_DIR = "images"

# ==========================================================================
# КОД БОТА. Ниже менять ничего не нужно.
# ==========================================================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


def tg_link() -> str:
    """Ссылка на письменный контакт с менеджером в Телеграме."""
    uname = MANAGER_TELEGRAM.lstrip("@")
    return f"https://t.me/{uname}"


def main_menu_kb() -> InlineKeyboardMarkup:
    """Главное меню — список категорий + прямой контакт менеджера."""
    rows = [
        [InlineKeyboardButton(text=data["title"], callback_data=f"cat:{code}")]
        for code, data in CATEGORIES.items()
    ]
    rows.append([InlineKeyboardButton(text="👨‍💼 Написати менеджеру", url=tg_link())])
    rows.append([InlineKeyboardButton(text="☎️ Зателефонувати менеджеру", callback_data="call")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def subs_kb(cat_code: str) -> InlineKeyboardMarkup:
    """Меню подкатегорий выбранной категории."""
    rows = [
        [InlineKeyboardButton(text=f"• {sub}", callback_data=f"sub:{cat_code}:{i}")]
        for i, sub in enumerate(CATEGORIES[cat_code]["subs"])
    ]
    rows.append([InlineKeyboardButton(text="⬅️ Назад до категорій", callback_data="home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def delivery_kb() -> InlineKeyboardMarkup:
    """Под-меню направлений доставки."""
    rows = [
        [InlineKeyboardButton(text=zone["title"], callback_data=f"zone:{code}")]
        for code, zone in DELIVERY_ZONES.items()
    ]
    rows.append([InlineKeyboardButton(text="⬅️ На головну", callback_data="home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def contact_kb() -> InlineKeyboardMarkup:
    """Финальный экран: два способа связи + возврат."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍💼 Написати менеджеру", url=tg_link())],
        [InlineKeyboardButton(text="☎️ Зателефонувати менеджеру", callback_data="call")],
        [InlineKeyboardButton(text="⬅️ На головну", callback_data="home")],
    ])


# ---- Обработчики ----------------------------------------------------------

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())


@dp.callback_query(F.data == "home")
async def go_home(cb: CallbackQuery):
    # На случай, если предыдущее сообщение было фото — edit_text упадёт, тогда шлём новое
    try:
        await cb.message.edit_text(WELCOME_TEXT, reply_markup=main_menu_kb())
    except Exception:
        await cb.message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())
    await cb.answer()


@dp.callback_query(F.data.startswith("cat:"))
async def open_category(cb: CallbackQuery):
    code = cb.data.split(":", 1)[1]
    cat = CATEGORIES.get(code)
    if not cat:
        await cb.answer("Категорію не знайдено", show_alert=True)
        return

    # Раздел «Доставка» — показываем под-меню направлений
    if code == "delivery":
        await cb.message.edit_text(
            "🚚 <b>Тарифи на доставку</b>\n\nОберіть напрямок:",
            reply_markup=delivery_kb(),
        )
        await cb.answer()
        return

    await cb.message.edit_text(
        f"{cat['title']}\n\nОберіть напрямок:",
        reply_markup=subs_kb(code),
    )
    await cb.answer()


@dp.callback_query(F.data.startswith("zone:"))
async def show_zone(cb: CallbackQuery):
    """Отправляет фото таблицы тарифов выбранного направления."""
    code = cb.data.split(":", 1)[1]
    zone = DELIVERY_ZONES.get(code)
    if not zone:
        await cb.answer("Напрямок не знайдено", show_alert=True)
        return

    path = os.path.join(IMAGES_DIR, zone["file"])
    caption = f"🚚 <b>Тарифи: {zone['title']}</b>"

    if os.path.exists(path):
        photo = FSInputFile(path)
        await cb.message.answer_photo(
            photo=photo,
            caption=caption,
            reply_markup=contact_kb(),
        )
    else:
        # Если файла нет — не падаем, а сообщаем понятно
        await cb.message.answer(
            f"{caption}\n\n(Зображення тимчасово недоступне. "
            "Уточніть тариф у менеджера.)",
            reply_markup=contact_kb(),
        )
    await cb.answer()


@dp.callback_query(F.data.startswith("sub:"))
async def open_sub(cb: CallbackQuery):
    _, code, idx = cb.data.split(":")
    sub_name = CATEGORIES[code]["subs"][int(idx)]
    text = (
        f"Ви обрали:\n<b>{sub_name}</b>\n\n"
        "Зв'яжіться з менеджером — підкажемо наявність, ціну та оформимо замовлення:"
    )
    await cb.message.edit_text(text, reply_markup=contact_kb())
    await cb.answer()


@dp.callback_query(F.data == "call")
async def show_phone(cb: CallbackQuery):
    text = (
        "☎️ <b>Телефон менеджера:</b>\n\n"
        f'<a href="tel:{MANAGER_PHONE}">{MANAGER_PHONE}</a>\n\n'
        "Натисніть на номер, щоб зателефонувати."
    )
    await cb.message.answer(text)
    await cb.answer()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
