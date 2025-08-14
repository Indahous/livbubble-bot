# bot.py
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

# ================
# Настройки
# ================

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

# Токен бота (обязательно через .env)
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ ОШИБКА: BOT_TOKEN не найден. Убедитесь, что файл .env существует и содержит BOT_TOKEN")

# URL Web App (должен быть задеплоен)
WEBAPP_URL = "https://livbubble-webapp.onrender.com"

# Список администраторов (только они могут управлять ботом)
ADMIN_IDS = []
admin_ids_str = os.getenv("ADMIN_IDS", "")
if admin_ids_str:
    try:
        ADMIN_IDS = [int(id.strip()) for id in admin_ids_str.split(",")]
    except ValueError:
        logging.getLogger(__name__).error("❌ Ошибка: ADMIN_IDS должен содержать только числа, разделённые запятыми")

# ================
# Списки спама
# ================

SPAM_KEYWORDS = [
    "FREE ETH", "FREEETHER.NET", "CLAIM ETH", "GET FREE CRYPTO",
    "BITCOIN GIVEAWAY", "ETHEREUM AIRDROP", "FREE CRYPTO",
    "CONNECT YOUR WALLET", "WALLET VERIFY", "FREE MONEY",
    "CLICK HERE", "INSTANT REWARDS", "NO REGISTRATION",
    "ABSOLUTELY FREE", "DROP ETH", "GIVEAWAY", "FREE NFT",
    "AIRDROP", "SEND ETHER", "FREE MONEY", "CRYPTO BONUS",
    "MAKE MONEY FAST", "PUMP MY WALLET", "VERIFICATION REQUIRED",
    "WALLET SYNC", "DEPOSIT TO CLAIM", "ABSOLUTELY FREE"
]

SPAM_DOMAINS = [
    "freeether.net", "free-eth.com", "claim-eth.org", "airdrop-crypto.ru",
    "getfreecrypto.io", "crypto-giveaway.net", "bitcoin-airdrop.org",
    "wallet-verify.com", "eth-drop.com", "free-crypto.today",
    "claimcrypto.pro", "airdrop-funds.com", "verifywallet.net",
    "bit-airdrop.com", "nft-giveaway.net"
]

# ================
# Логирование
# ================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================
# Бот и диспетчер
# ================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ================
# Команда /start
# ================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """
    Отправляет приветствие и кнопку для запуска Web App.
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎮 Начать игру",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )]
    ])

    welcome_text = (
        "🎮 Добро пожаловать в **Liv Bubble**!\n\n"
        "Вы подписаны — начинайте игру и участвуйте в розыгрыше каждый день в 12:00!"
    )

    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")

# ================
# Функция проверки спама
# ================

def is_spam(text: str) -> bool:
    """
    Проверяет текст на признаки спама.
    Возвращает True, если спам найден.
    """
    if not text:
        return False

    text_upper = text.upper()
    text_lower = text.lower()

    # Проверка по доменам (самый точный способ)
    for domain in SPAM_DOMAINS:
        if domain in text_lower:
            return True

    # Проверка по ключевым словам
    spam_signals = sum(1 for keyword in SPAM_KEYWORDS if keyword in text_upper)
    return spam_signals >= 2  # Требуется минимум 2 совпадения

# ================
# Обработчик спама
# ================

@dp.message()
async def filter_spam(message: types.Message):
    """
    Удаляет спам-сообщения, ссылки, подписи.
    Пропускает администраторов и команды.
    """
    # Пропускаем админов
    if message.from_user.id in ADMIN_IDS:
        return

    # Пропускаем команды (важно!)
    if message.text and message.text.startswith('/'):
        return  # ← Ключевое: не блокируем команды

    # Блокировка пересланных сообщений
    if message.forward_date:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        logger.warning(f"Удалено пересланное сообщение от {message.from_user.id}")
        return

    # Проверка текста
    if message.text and is_spam(message.text):
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await message.answer("❌ Спам-сообщение удалено.")
        logger.warning(f"Спам удалён от {message.from_user.id}: {message.text}")
        return

    # Проверка подписи
    if message.caption and is_spam(message.caption):
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await message.answer("❌ Спам в подписи удалён.")
        logger.warning(f"Спам в подписи удалён от {message.from_user.id}")
        return

    # Проверка URL в тексте
    if message.entities:
        for entity in message.entities:
            if entity.type == "url":
                url = message.text[entity.offset:entity.offset + entity.length].lower()
                if any(domain in url for domain in SPAM_DOMAINS):
                    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
                    await message.answer("❌ Подозрительная ссылка удалена.")
                    logger.warning(f"Подозрительная ссылка удалена: {url}")
                    return

# ================
# Обработка данных из Web App
# ================

@dp.message()
async def handle_web_app_data(message: types.Message):
    """
    Обрабатывает данные, отправленные из Web App через Telegram.WebApp.sendData()
    """
    if not message.web_app_data:
        return

    try:
        data = message.web_app_data.data

        if "game_completed" in data:
            bubbles = data.split('bubbles_popped":')[1].split('}')[0] if 'bubbles_popped' in data else "неизвестно"
            await message.answer(
                f"🎉 Поздравляем! Ты успешно завершил игру!\n"
                f"Лопнул пузырей: {bubbles}\n\n"
                "Ты выполнил все задания. Жди награду!"
            )
        elif "task_completed" in data:
            task_id = data.split('task_id":')[1].split('}')[0] if 'task_id' in data else "неизвестно"
            await message.answer(f"✅ Задание #{task_id} выполнено!")
    except Exception as e:
        logger.error(f"Ошибка обработки WebAppData: {e}")
        await message.answer("⚠️ Ошибка при обработке данных.")

# ================
# Запуск бота
# ================

async def main():
    logger.info("✅ Бот запущен и готов к работе...")
    logger.info("🌐 Ожидание сообщений...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен вручную.")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
