# bot.py
import asyncio
import logging
import os
import json
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

# ================
# Настройка логирования (сразу в начале)
# ================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ================
# Загрузка переменных окружения
# ================

try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("✅ .env загружен")
except ImportError:
    logger.warning("⚠️ Модуль dotenv не установлен — используем переменные окружения напрямую")

# ================
# Переменные окружения
# ================

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ ОШИБКА: BOT_TOKEN не найден. Убедитесь, что переменная задана в Render")

WEBAPP_URL = os.getenv("WEBAPP_URL", "https://livbubble-webapp.onrender.com")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@livbubble")

# Список администраторов
ADMIN_IDS = []
admin_ids_str = os.getenv("ADMIN_IDS", "")
if admin_ids_str:
    try:
        ADMIN_IDS = [int(id.strip()) for id in admin_ids_str.split(",")]
    except ValueError:
        logger.error("❌ Ошибка: ADMIN_IDS должен содержать только числа")

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
# Бот и диспетчер
# ================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ================
# Команда /start
# ================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id

    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ["member", "administrator", "creator"]:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="🎮 Начать игру",
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )]
            ])
            await message.answer(
                "🎮 Добро пожаловать в <b>Liv Bubble</b>!\n\n"
                "Вы подписаны — начинайте игру и участвуйте в розыгрыше каждый день в 12:00!",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="📢 Подписаться на канал",
                    url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"
                )]
            ])
            await message.answer(
                "⚠️ Чтобы играть, вы должны быть подписаны на канал @livbubble.\n\n"
                "Подпишитесь и нажмите /start, чтобы начать игру.",
                reply_markup=keyboard
            )
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}")
        await message.answer("❌ Произошла ошибка при проверке подписки. Попробуйте позже.")

# ================
# Функция проверки спама
# ================

def is_spam(text: str) -> bool:
    if not text:
        return False
    text_upper = text.upper()
    text_lower = text.lower()
    for domain in SPAM_DOMAINS:
        if domain in text_lower:
            return True
    spam_signals = sum(1 for keyword in SPAM_KEYWORDS if keyword in text_upper)
    return spam_signals >= 2

# ================
# Обработчик спама
# ================

@dp.message()
async def filter_spam(message: Message):
    """
    Удаляет спам, но пропускает команды и админов.
    ВАЖНО: после /start, чтобы не блокировать /start
    """
    logger.info(f"Получено сообщение от {message.from_user.id}: {message.text or '[без текста]'}")

    # Пропускаем админов
    if message.from_user.id in ADMIN_IDS:
        return

    # Пропускаем команды
    if message.text and message.text.startswith('/'):
        return

    # Блокировка пересланных сообщений
    if message.forward_date:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        except Exception as e:
            logger.warning(f"Не удалось удалить пересланное сообщение: {e}")
        return

    # Проверка текста
    if message.text and is_spam(message.text):
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            await message.answer("❌ Спам-сообщение удалено.")
        except Exception as e:
            logger.warning(f"Ошибка при удалении спама: {e}")
        return

    # Проверка подписи
    if message.caption and is_spam(message.caption):
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            await message.answer("❌ Спам в подписи удалён.")
        except Exception as e:
            logger.warning(f"Ошибка при удалении спама в подписи: {e}")
        return

    # Проверка URL
    if message.entities:
        for entity in message.entities:
            if entity.type == "url":
                url = message.text[entity.offset:entity.offset + entity.length].lower()
                if any(domain in url for domain in SPAM_DOMAINS):
                    try:
                        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
                        await message.answer("❌ Подозрительная ссылка удалена.")
                    except Exception as e:
                        logger.warning(f"Ошибка при удалении ссылки: {e}")
                    return

# ================
# Обработка данных из Web App
# ================

@dp.message(F.web_app_data)
async def handle_web_app_data(message: Message):
    logger.info(f"Получены данные из Web App от {message.from_user.id}: {message.web_app_data.data}")

    try:
        data = json.loads(message.web_app_data.data)
        if data.get("game_completed"):
            bubbles = data.get("bubbles_popped", "неизвестно")
            await message.answer(
                f"🎉 Поздравляем! Ты успешно завершил игру!\n"
                f"Лопнул пузырей: {bubbles}\n\n"
                "Ты выполнил все задания. Жди награду!"
            )
        elif data.get("task_completed"):
            task_id = data.get("task_id", "неизвестно")
            await message.answer(f"✅ Задание #{task_id} выполнено!")
    except Exception as e:
        logger.error(f"Ошибка обработки WebAppData: {e}")
        await message.answer("⚠️ Ошибка при обработке данных.")

# ================
# Запуск бота
# ================

async def main():
    logger.info("✅ Бот запущен и готов к работе...")
    try:
        import requests
        response = requests.get(WEBAPP_URL, timeout=5)
        if response.status_code == 200:
            logger.info(f"✅ Web App доступен по адресу: {WEBAPP_URL}")
        else:
            logger.warning(f"⚠️ Web App недоступен. Статус: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Ошибка проверки Web App: {e}")

    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        logger.info("🚀 Запуск бота...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен вручную.")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)
