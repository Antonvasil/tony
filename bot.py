# -*- coding: utf-8 -*-
"""
Telegram-бот для компании стройматериалов (Киев).
Пилотная версия: дерево категорий -> подкатегории -> контакт менеджера.
Библиотека: aiogram 3.x

КАК ЗАПУСТИТЬ (кратко, подробно — в инструкции отдельным файлом):
1. Установить Python 3.10+
2. pip install aiogram
3. Вставить токен бота в BOT_TOKEN ниже (получить у @BotFather)
4. python bot.py
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
)

# ==========================================================================
# НАСТРОЙКИ — всё, что нужно менять, лежит здесь. Код ниже трогать не нужно.
# ==========================================================================

# Токен бота от @BotFather.
# На сервере (Railway) он задаётся в настройках как переменная BOT_TOKEN.
# Для запуска на своём компе можно временно вписать токен во вторые кавычки.
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Номер и контакт менеджера
MANAGER_PHONE = "+380670080788"
MANAGER_TELEGRAM = "@username_менеджера"   # <-- заменить на реальный юзернейм для письменного контакта

# Текст на стартовом экране (баннер-картинку добавим позже отдельно)
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
# Формат: "код": {"title": "текст кнопки", "subs": ["подкатегория 1", ...]}
# Чтобы добавить/убрать категорию или подкатегорию — просто правь этот словарь.
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
        "subs": [],   # особый раздел: тут покажем фото/текст тарифов, не подкатегории
    },
}

# Текст для раздела доставки (потом заменим на фото таблицы, когда клиент пришлёт)
DELIVERY_TEXT = (
    "🚚 <b>Тарифи на доставку</b>\n\n"
    "Актуальні тарифи уточнюйте у менеджера — надішлемо таблицю з цінами.\n"
    "(Тут буде фото з тарифами.)"
)

# ==========================================================================
# КОД БОТА. Ниже менять ничего не нужно.
# ==========================================================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


def main_menu_kb() -> InlineKeyboardMarkup:
    """Главное меню — список категорий + прямой контакт менеджера."""
    rows = [
        [InlineKeyboardButton(text=data["title"], callback_data=f"cat:{code}")]
        for code, data in CATEGORIES.items()
    ]
    # Кнопки контакта прямо в главном меню (быстрый путь)
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


def contact_kb() -> InlineKeyboardMarkup:
    """Финальный экран: два способа связи + возврат."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍💼 Написати менеджеру", url=tg_link())],
        [InlineKeyboardButton(text="☎️ Зателефонувати менеджеру", callback_data="call")],
        [InlineKeyboardButton(text="⬅️ На головну", callback_data="home")],
    ])


def tg_link() -> str:
    """Ссылка на письменный контакт с менеджером в Телеграме."""
    uname = MANAGER_TELEGRAM.lstrip("@")
    return f"https://t.me/{uname}"


# ---- Обработчики ----------------------------------------------------------

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())


@dp.callback_query(F.data == "home")
async def go_home(cb: CallbackQuery):
    await cb.message.edit_text(WELCOME_TEXT, reply_markup=main_menu_kb())
    await cb.answer()


@dp.callback_query(F.data.startswith("cat:"))
async def open_category(cb: CallbackQuery):
    code = cb.data.split(":", 1)[1]
    cat = CATEGORIES.get(code)
    if not cat:
        await cb.answer("Категорію не знайдено", show_alert=True)
        return

    # Особый раздел «Доставка» — сразу показываем тарифы, без подкатегорий
    if code == "delivery":
        await cb.message.edit_text(
            DELIVERY_TEXT,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👨‍💼 Написати менеджеру", url=tg_link())],
                [InlineKeyboardButton(text="☎️ Зателефонувати менеджеру", callback_data="call")],
                [InlineKeyboardButton(text="⬅️ На головну", callback_data="home")],
            ]),
        )
        await cb.answer()
        return

    await cb.message.edit_text(
        f"{cat['title']}\n\nОберіть напрямок:",
        reply_markup=subs_kb(code),
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
    # В Телеграме кнопка не запускает звонок сама — показываем кликабельный номер.
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
