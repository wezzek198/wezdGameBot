import logging
import random
import re
import json
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler, JobQueue

# Настройка логирования в файл
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot_activity.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# НАСТРОЙКИ - ЗАМЕНИТЕ НА СВОИ!
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_USERNAME = "wezdgame"  # БЕЗ @ !!!
OWNER_ID = 1307172745  # Ваш ID в Telegram

# ПАПКА ДЛЯ ДАННЫХ
DATA_FOLDER = "data"  # Папка для хранения данных

# Файлы для сохранения данных
DATA_FILE = os.path.join(DATA_FOLDER, "wordle_data.json")

# БАЗА СЛОВ РАЗНЫХ УРОВНЕЙ СЛОЖНОСТИ
WORD_DATABASE = {
    1: {  # Легкий - 3-4 буквы
        "name": "🍀 Начинающий",
        "points": 10,
        "min_length": 3,
        "max_length": 4,
        "words": [
            "кот", "дом", "сад", "нос", "рот", "год", "день", "ночь", "рука", "нога",
            "вода", "огонь", "земля", "воздух", "мама", "папа", "сын", "дочь", "брат",
            "сестра", "стол", "стул", "книга", "ручка", "тетрадь", "школа", "учитель",
            "ученик", "друг", "враг", "мир", "война", "любовь", "ненависть", "счастье",
            "горе", "радость", "печаль", "зима", "лето", "весна", "осень", "солнце",
            "луна", "звезда", "небо", "облако", "дождь", "снег", "ветер", "море", "река"
        ]
    },
    2: {  # Средний - 5-6 букв
        "name": "🌿 Любитель", 
        "points": 25,
        "min_length": 5,
        "max_length": 6,
        "words": [
            "компьютер", "телефон", "программа", "сообщение", "картина",
            "музыка", "театр", "кино", "спорт", "футбол", "хоккей",
            "баскетбол", "теннис", "плавание", "победа", "чемпион",
            "рекорд", "стадион", "арена", "зал", "тренировка", "медаль",
            "кубок", "приз", "награда", "праздник", "юбилей", "свадьба",
            "путешествие", "приключение", "открытие", "вдохновение"
        ]
    },
    3: {  # Сложный - 7-8 букв
        "name": "🌲 Профессионал",
        "points": 50,
        "min_length": 7,
        "max_length": 8,
        "words": [
            "программирование", "алгоритм", "информация", "коммуникация",
            "образование", "лаборатория", "исследование", "эксперимент",
            "открытие", "изобретение", "технология", "инновация", "модернизация",
            "автоматизация", "роботизация", "искусственный", "интеллект", "нейросеть",
            "криптография", "безопасность", "шифрование", "дешифровка",
            "биотехнология", "космонавтика", "астрономия", "астрофизика",
            "гравитация", "эволюция", "революция", "демократия"
        ]
    },
    4: {  # Очень сложный - 9-10 букв
        "name": "🔥 Эксперт",
        "points": 100,
        "min_length": 9,
        "max_length": 10,
        "words": [
            "интеллектуальность", "энциклопедичность", "многофункциональность",
            "высокотехнологичный", "сверхпроводимость", "электропроводность",
            "термоядерный", "радиоактивность", "полупроводниковый",
            "трансформаторный", "конструкторский", "проектировочный",
            "архитектурный", "градостроительный", "ландшафтный",
            "агропромышленный", "металлургический", "машиностроительный",
            "судостроительный", "авиастроительный", "ракетостроительный",
            "космодромный", "орбитальный", "телевизионный", "радиостанционный"
        ]
    },
    5: {  # Экспертный - 11-15 букв
        "name": "💀 Мастер",
        "points": 200,
        "min_length": 11,
        "max_length": 15,
        "words": [
            "электромагнитный", "гидроэлектростанция", "теплоэлектростанция",
            "радиолокационный", "фотоэлектрический", "гидроакустический",
            "сейсмостойкий", "метеорологический", "океанографический", "палеонтологический", "археологический", "антропологический",
            "этнографический", "лингвистический", "филологический",
            "психологический", "социологический", "философский",
            "идеологический", "методологический", "теоретический",
            "практический", "экспериментальный", "исследовательский"
        ]
    },
    6: {  # Легендарный - 16+ букв (ДВА СЛОВА С ПРОБЕЛОМ!)
        "name": "👑 Легенда",
        "points": 500,
        "min_length": 16,
        "max_length": 30,
        "words": [
            "высоковольтный трансформатор", "полупроводниковый диод",
            "интегральная микросхема", "микропроцессорное устройство",
            "операционная система", "прикладное программное обеспечение",
            "системное программирование", "прикладное программирование",
            "искусственный интеллект", "виртуальная реальность",
            "дополненная реальность", "нейронные сети", "глубинное обучение",
            "блокчейн технология", "криптовалютный кошелек",
            "децентрализованный реестр", "распределенный регистр",
            "электронно цифровая подпись", "автоматизированное рабочее место",
            "квантовый компьютер", "теория относительности",
            "международная космическая станция", "искусственный спутник земли"
        ]
    },
    7: {  # Свободный режим для друзей
        "name": "🎯 Свободный режим",
        "points": 0,  # Без очков, только для развлечения
        "min_length": 3,
        "max_length": 30,
        "words": []  # Пользователь сам вводит слово
    }
}

# Хранилище данных
user_games = {}  # {user_id: {'word': 'слово', 'guesses': [], 'level': X, 'game_type': 'bot' или 'friend'}}
waiting_for_word = {}  # Пользователи, которые загадывают слово (только для свободного режима)
waiting_for_level = {}  # Пользователи, которые выбирают уровень
used_words = set()  # Уже отгаданные слова
game_links = {}  # {game_id: {'creator_id': X, 'word': 'слово', 'level': Y, 'game_type': 'bot' или 'friend'}}
leaderboard = {}
weekly_stats = {}
user_stats = {}
active_games = {}  # {game_id: {'creator': X, 'word': 'word', 'level': Z, 'game_type': 'bot' или 'friend', 'players': [user_ids]}}
user_progress = {}  # {user_id: {level: [отгаданные_слова], 'max_level': X, 'total_words': Y}}

async def notify_owner(context: ContextTypes.DEFAULT_TYPE, message: str):
    """Отправляет уведомление владельцу"""
    try:
        await context.bot.send_message(OWNER_ID, message, parse_mode='Markdown')
        logging.info(f"Уведомление отправлено владельцу: {message[:50]}...")
    except Exception as e:
        logging.error(f"Ошибка отправки уведомления владельцу: {e}")

def save_data():
    """Сохраняет данные в файл"""
    data = {
        'user_games': user_games,
        'waiting_for_word': waiting_for_word,
        'waiting_for_level': waiting_for_level,
        'used_words': list(used_words),
        'game_links': game_links,
        'leaderboard': leaderboard,
        'weekly_stats': weekly_stats,
        'user_stats': user_stats,
        'active_games': active_games,
        'user_progress': user_progress,
        'last_save': datetime.now().isoformat()
    }
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Ошибка сохранения данных: {e}")

def load_data():
    """Загружает данные из файла"""
    global user_games, waiting_for_word, waiting_for_level, used_words, game_links, leaderboard, weekly_stats, user_stats, active_games, user_progress
    
    # Создаем папку для данных если ее нет
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
    
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                user_games = data.get('user_games', {})
                waiting_for_word = data.get('waiting_for_word', {})
                waiting_for_level = data.get('waiting_for_level', {})
                used_words = set(data.get('used_words', []))
                game_links = data.get('game_links', {})
                leaderboard = data.get('leaderboard', {})
                weekly_stats = data.get('weekly_stats', {})
                user_stats = data.get('user_stats', {})
                active_games = data.get('active_games', {})
                user_progress = data.get('user_progress', {})
            logging.info(f"✅ Данные загружены: {len(leaderboard)} пользователей, {len(user_stats)} статистик")
        except Exception as e:
            logging.error(f"Ошибка загрузки данных: {e}")
            reset_all_data()
    else:
        reset_all_data()
        logging.info("Создана новая база данных")

def reset_all_data():
    """Сбрасывает все данные"""
    global user_games, waiting_for_word, waiting_for_level, used_words, game_links, leaderboard, weekly_stats, user_stats, active_games, user_progress
    user_games = {}
    waiting_for_word = {}
    waiting_for_level = {}
    used_words = set()
    game_links = {}
    leaderboard = {}
    weekly_stats = {}
    user_stats = {}
    active_games = {}
    user_progress = {}

async def reset_weekly_stats(context: ContextTypes.DEFAULT_TYPE):
    """Сбрасывает недельную статистику"""
    global weekly_stats
    
    if not weekly_stats:
        logging.info("Недельная статистика пуста, сброс не требуется")
        return
    
    logging.info("🏆 Автоматический сброс недельной статистики...")
    
    # Находим победителей недели
    sorted_weekly = sorted(weekly_stats.items(), key=lambda x: x[1]['points'], reverse=True)
    
    # Отправляем уведомления победителям
    winners_text = "🏆 *НЕДЕЛЬНЫЕ ПОБЕДИТЕЛИ!*\n\n"
    winners_text += "Неделя завершена! Вот топ игроков:\n\n"
    
    top_winners = []
    for i, (user_id, data) in enumerate(sorted_weekly[:3], 1):
        if i == 1:
            medal = "🥇"
            reward = "500 очков + VIP статус!"
        elif i == 2:
            medal = "🥈" 
            reward = "300 очков"
        else:
            medal = "🥉"
            reward = "150 очков"
        
        top_winners.append({
            'id': user_id,
            'name': data['name'],
            'points': data['points'],
            'wins': data['games_won'],
            'medal': medal,
            'reward': reward
        })
        
        winners_text += f"{medal} *{data['name']}*\n"
        winners_text += f"   ⭐ Очков: {data['points']}\n"
        winners_text += f"   🏅 Побед: {data['games_won']}\n"
        winners_text += f"   🎁 Награда: {reward}\n\n"
    
    winners_text += "🎁 *Как получить награды:*\n"
    winners_text += f"1. Перейди в наш канал: @{CHANNEL_USERNAME}\n"
    winners_text += "2. Напиши свой ID и место в топе\n"
    winners_text += "3. Получи приз в течение 24 часов!\n\n"
    winners_text += "🎮 Новая неделя началась! Удачи всем! 🚀"
    
    # Отправляем уведомления победителям
    for winner in top_winners:
        try:
            await context.bot.send_message(winner['id'], winners_text, parse_mode='Markdown')
            logging.info(f"Уведомление отправлено победителю {winner['name']} (ID: {winner['id']})")
        except Exception as e:
            logging.error(f"Не удалось отправить уведомление пользователю {winner['id']}: {e}")
    
    # Начисляем награды в общую таблицу лидеров
    for i, (user_id, data) in enumerate(sorted_weekly[:3], 1):
        if user_id not in leaderboard:
            leaderboard[user_id] = {'total_points': 0, 'total_wins': 0, 'name': data['name']}
        
        if i == 1:
            leaderboard[user_id]['total_points'] += 500
        elif i == 2:
            leaderboard[user_id]['total_points'] += 300
        elif i == 3:
            leaderboard[user_id]['total_points'] += 150
    
    # Сбрасываем недельную статистику
    weekly_stats = {}
    save_data()
    
    await notify_owner(context, "✅ *Недельная статистика сброшена автоматически!*\n\n"
                         f"Время сброса: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                         "Новая неделя началась! 🎉")
    
    logging.info("✅ Недельная статистика сброшена!")

async def manual_weekly_reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для ручного сброса статистики (только для владельца)"""
    user = update.effective_user
    
    if user.id != OWNER_ID:
        await update.message.reply_text("❌ Эта команда только для владельца бота!")
        return
    
    await reset_weekly_stats(context)
    
    await update.message.reply_text("✅ Недельная статистика сброшена вручную!")

async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверяет, подписан ли пользователь на канал"""
    try:
        chat = await context.bot.get_chat(f"@{CHANNEL_USERNAME}")
        logging.info(f"Канал найден: {chat.title}")
        
        try:
            member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
            is_subscribed = member.status in ['member', 'administrator', 'creator']
            logging.info(f"Статус пользователя {user_id} в канале: {member.status}, подписан: {is_subscribed}")
            return is_subscribed
        except Exception as e:
            logging.warning(f"Пользователь {user_id} не подписан на канал: {e}")
            return False
    except Exception as e:
        logging.error(f"Ошибка доступа к каналу @{CHANNEL_USERNAME}: {e}")
        # Если канал недоступен, считаем что проверка прошла
        return True

async def update_leaderboard(user_id: int, user_name: str, points: int, game_type: str = "bot"):
    """Обновляет таблицу лидеров"""
    # Общая статистика
    if user_id not in leaderboard:
        leaderboard[user_id] = {
            'total_points': 0, 
            'total_wins': 0, 
            'name': user_name, 
            'bot_wins': 0,
            'friend_wins': 0
        }
    
    if game_type == "bot":
        leaderboard[user_id]['bot_wins'] += 1
    elif game_type == "friend":
        leaderboard[user_id]['friend_wins'] += 1
    
    leaderboard[user_id]['total_wins'] += 1
    leaderboard[user_id]['total_points'] += points
    
    # Недельная статистика
    if user_id not in weekly_stats:
        weekly_stats[user_id] = {'points': 0, 'games_won': 0, 'name': user_name}
    
    weekly_stats[user_id]['points'] += points
    weekly_stats[user_id]['games_won'] += 1
    
    # Подробная статистика пользователя
    if user_id not in user_stats:
        user_stats[user_id] = {
            'name': user_name,
            'games_played': 0,
            'games_won': 0,
            'total_points': 0,
            'best_level': 0,
            'bot_games': 0,
            'friend_games': 0,
            'last_played': datetime.now().isoformat(),
            'first_seen': datetime.now().isoformat(),
            'words_guessed': 0
        }
    
    user_stats[user_id]['games_played'] += 1
    user_stats[user_id]['games_won'] += 1
    user_stats[user_id]['total_points'] += points
    user_stats[user_id]['last_played'] = datetime.now().isoformat()
    user_stats[user_id]['words_guessed'] += 1
    
    if game_type == "bot":
        user_stats[user_id]['bot_games'] += 1
    else:
        user_stats[user_id]['friend_games'] += 1
    
    save_data()

def get_user_progress(user_id: int, level: int = None):
    """Получает прогресс пользователя"""
    if user_id not in user_progress:
        user_progress[user_id] = {
            'max_level': 1,  # Начинают с первого уровня
            'total_words': 0,
            'levels': {}
        }
    
    if level is not None:
        if level not in user_progress[user_id]['levels']:
            user_progress[user_id]['levels'][level] = []
    
    return user_progress[user_id]

def update_user_progress(user_id: int, level: int, word: str):
    """Обновляет прогресс пользователя"""
    progress = get_user_progress(user_id, level)
    
    if word not in progress['levels'].get(level, []):
        if level not in progress['levels']: progress['levels'][level] = []
        progress['levels'][level].append(word)
        progress['total_words'] += 1
        
        # Проверяем, все ли слова уровня отгаданы
        total_words_in_level = len(WORD_DATABASE[level]['words'])
        guessed_words = len(progress['levels'].get(level, []))
        
        if guessed_words >= total_words_in_level and level < 6:  # 6 - последний основной уровень
            # Открываем следующий уровень
            next_level = level + 1
            if next_level <= 6 and next_level > progress['max_level']:
                progress['max_level'] = next_level
                logging.info(f"Пользователь {user_id} открыл уровень {next_level}")
        
        save_data()
        return True
    return False

def is_level_unlocked(user_id: int, level: int):
    """Проверяет, открыт ли уровень для пользователя"""
    if level == 1:
        return True  # Первый уровень всегда открыт
    
    progress = get_user_progress(user_id)
    return level <= progress['max_level']

def get_available_words(user_id: int, level: int):
    """Получает доступные слова для уровня (неотгаданные)"""
    progress = get_user_progress(user_id, level)
    guessed_words = set(progress['levels'].get(level, []))
    all_words = WORD_DATABASE[level]['words']
    
    available = [word for word in all_words if word not in guessed_words]
    return available

async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает таблицу лидеров"""
    if not leaderboard:
        if hasattr(update, 'callback_query'):
            await update.callback_query.edit_message_text("📊 Таблица лидеров пока пуста! Сыграй первую игру!")
        else:
            await update.message.reply_text("📊 Таблица лидеров пока пуста! Сыграй первую игру!")
        return
    
    # Топ по очкам
    sorted_by_points = sorted(leaderboard.items(), key=lambda x: x[1]['total_points'], reverse=True)
    
    leaderboard_text = "🏆 *ТОП-10 ИГРОКОВ (все время):*\n\n"
    
    for i, (user_id, data) in enumerate(sorted_by_points[:10], 1):
        medal = ""
        if i == 1: medal = "🥇"
        elif i == 2: medal = "🥈"
        elif i == 3: medal = "🥉"
        else: medal = f"{i}."
        
        leaderboard_text += f"{medal} *{data['name']}*\n"
        leaderboard_text += f"   ⭐ Очков: {data['total_points']}\n"
        leaderboard_text += f"   🏅 Всего побед: {data['total_wins']}\n"
        leaderboard_text += f"   🤖 Побед с ботом: {data.get('bot_wins', 0)}\n"
        leaderboard_text += f"   👥 Побед с друзьями: {data.get('friend_wins', 0)}\n\n"
    
    # Недельный топ
    if weekly_stats:
        sorted_weekly = sorted(weekly_stats.items(), key=lambda x: x[1]['points'], reverse=True)
        
        leaderboard_text += "📅 *НЕДЕЛЬНЫЙ ТОП-5:*\n\n"
        
        for i, (user_id, data) in enumerate(sorted_weekly[:5], 1):
            medal = ""
            if i == 1: medal = "🥇"
            elif i == 2: medal = "🥈"
            elif i == 3: medal = "🥉"
            else: medal = f"{i}."
            
            leaderboard_text += f"{medal} *{data['name']}* - {data['points']} очков ({data['games_won']} побед)\n"
        
        leaderboard_text += "\n🎁 *Недельные награды:*\n"
        leaderboard_text += "🥇 1 место: 500 очков + VIP статус\n"
        leaderboard_text += "🥈 2 место: 300 очков\n"
        leaderboard_text += "🥉 3 место: 150 очков\n\n"
        leaderboard_text += f"📢 *Чтобы получить награды, зайдите в канал:* @{CHANNEL_USERNAME}\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if hasattr(update, 'callback_query'):
        await update.callback_query.edit_message_text(leaderboard_text, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        await update.message.reply_text(leaderboard_text, parse_mode='Markdown', reply_markup=reply_markup)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    try:
        user = update.effective_user
        user_id = user.id
        username = f"@{user.username}" if user.username else "Нет username"
        full_name = user.full_name
        
        # Логируем запуск бота
        logging.info(f"🚀 /start от {full_name} (ID: {user_id}, Username: {username})")
        
        # Уведомляем владельца о новом пользователе
        if user_id not in user_stats:
            await notify_owner(context, f"👤 *НОВЫЙ ПОЛЬЗОВАТЕЛЬ!*\n\n"
                                  f"Имя: {full_name}\n"
                                  f"ID: `{user_id}`\n"
                                  f"Username: {username}\n"
                                  f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        
        # Проверяем, есть ли параметры в /start
        if context.args:
            # Это переход по ссылке, проверяем подписку
            is_subscribed = await check_subscription(user_id, context)
            if not is_subscribed:
                await show_subscription_required(update, context)
                return
        
        # Получаем прогресс пользователя
        progress = get_user_progress(user_id)
        
        keyboard = [
            [InlineKeyboardButton("🎮 Играть с ботом", callback_data="play_with_bot")],
            [InlineKeyboardButton("👥 Играть с другом", callback_data="play_with_friend")],
            [InlineKeyboardButton("📊 Таблица лидеров", callback_data="leaderboard")],
            [InlineKeyboardButton("👤 Моя статистика", callback_data="my_stats")],
            [InlineKeyboardButton("📖 Правила", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = f"🎮 *Привет, {user.first_name}!*\n\n"
        welcome_text += "Я бот для игры в Wordle! Выбери режим игры:\n\n"
        welcome_text += "🤖 *Играть с ботом* - отгадывай слова разной сложности, получай очки!\n"
        welcome_text += "👥 *Играть с другом* - загадывай слово сам и отправляй ссылку другу!\n\n"
        
        # Показываем прогресс
        welcome_text += f"📈 *Твой прогресс:* Уровень {progress['max_level']}/6\n"
        welcome_text += f"📊 Отгадано слов: {progress['total_words']}\n\n"
        
        welcome_text += "*🎁 Недельные призы:*\n"
        welcome_text += "Топ-3 игрока каждой недели получают бонусные очки!\n"
        welcome_text += f"Подробности в канале: @{CHANNEL_USERNAME}"
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                welcome_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                welcome_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
    except Exception as e:
        logging.error(f"Ошибка в функции start: {e}")
        if hasattr(update, 'message'):
            await update.message.reply_text("Произошла ошибка. Попробуйте еще раз.")

async def show_subscription_required(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает сообщение о необходимости подписки"""
    keyboard = [
        [InlineKeyboardButton("📢 Подписаться на канал", url=f"https://t.me/{CHANNEL_USERNAME}")],
        [InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        if hasattr(update, 'message'):
            await update.message.reply_text(
                "📢 *Для использования бота необходимо подписаться на наш канал!*\n\n"
                "После подписки ты сможешь:\n"
                "• Играть в Wordle\n"
                "• Получать недельные награды\n"
                "• Участвовать в турнирах\n\n"
                f"Канал: @{CHANNEL_USERNAME}\n\n"
                "Подпишись и нажми 'Я подписался'", parse_mode='Markdown',
                reply_markup=reply_markup
            )
        elif hasattr(update, 'callback_query'):
            await update.callback_query.edit_message_text(
                "📢 *Для использования бота необходимо подписаться на наш канал!*\n\n"
                "После подписки ты сможешь:\n"
                "• Играть в Wordle\n"
                "• Получать недельные награды\n"
                "• Участвовать в турнирах\n\n"
                f"Канал: @{CHANNEL_USERNAME}\n\n"
                "Подпишись и нажми 'Я подписался'",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
    except Exception as e:
        logging.error(f"Ошибка в show_subscription_required: {e}")

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    logging.info(f"🔘 Кнопка {query.data} от {user.full_name} (ID: {user.id})")
    
    try:
        if query.data == "check_subscription":
            try:
                if await check_subscription(user.id, context):
                    await query.edit_message_text(
                        f"✅ *Отлично! Ты подписан на канал!*\n\n"
                        f"Теперь ты можешь использовать бота 🎮\n"
                        f"Нажми /start для начала игры!",
                        parse_mode='Markdown'
                    )
                else:
                    keyboard = [
                        [InlineKeyboardButton("📢 Подписаться на канал", url=f"https://t.me/{CHANNEL_USERNAME}")],
                        [InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(
                        "❌ *Ты еще не подписался на канал!*\n\n"
                        "Пожалуйста, подпишись на канал и нажми кнопку проверки еще раз.",
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
            except Exception as e:
                logging.error(f"Ошибка при проверке подписки: {e}")
                await query.edit_message_text(
                    "⚠️ *Не удалось проверить подписку.*\n\n"
                    "Попробуйте подписаться на канал и проверить еще раз.\n"
                    f"Канал: @{CHANNEL_USERNAME}",
                    parse_mode='Markdown'
                )
        
        elif query.data == "play_with_bot":
            # Проверяем подписку
            if not await check_subscription(user.id, context):
                await show_subscription_required(update, context)
                return
            await choose_bot_level(update, context)
        
        elif query.data == "play_with_friend":
            # Проверяем подписку
            if not await check_subscription(user.id, context):
                await show_subscription_required(update, context)
                return
            await choose_friend_level(update, context)
        
        elif query.data == "leaderboard":
            await show_leaderboard_callback(update, context)
        
        elif query.data == "my_stats":
            await show_my_stats(update, context)
        
        elif query.data == "help":
            await help_command_callback(update, context)
        
        elif query.data == "back_to_main":
            await start(update, context)
        
        elif query.data == "friend_bot_words":
            # Проверяем подписку
            if not await check_subscription(user.id, context):
                await show_subscription_required(update, context)
                return
            await choose_friend_bot_level(update, context)
        
        elif query.data.startswith("bot_level_"):
            # Проверяем подписку
            if not await check_subscription(user.id, context):
                await show_subscription_required(update, context)
                return
            level = int(query.data.split("_")[2])
            await start_bot_game(update, context, level)
        
        elif query.data.startswith("friend_level_"):
            # Проверяем подписку
            if not await check_subscription(user.id, context):
                await show_subscription_required(update, context)
                return
            level = int(query.data.split("_")[2])
            user_id = query.from_user.id
            
            if level == 7:  # Свободный режим
                waiting_for_word[user_id] = True
                waiting_for_level[user_id] = level
                
                level_info = WORD_DATABASE[level]
                
                keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="play_with_friend")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"🎯 *Свободный режим для друзей*\n\n"
                    f"Ты сам загадываешь любое русское слово\n"
                    f"Длина: {level_info['min_length']}-{level_info['max_length']} букв\n"
                    f"⚠️ *Без очков, только для развлечения!*\n\n"
                    f"📝 Введи слово, которое хочешь загадать:",
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            else:
                await start_bot_game_for_friend(update, context, level)
        
        elif query.data.startswith("friend_bot_level_"):
            # Проверяем подписку
            if not await check_subscription(user.id, context):
                await show_subscription_required(update, context)
                return
            level = int(query.data.split("_")[3])
            await start_bot_game_for_friend(update, context, level)
    
    except Exception as e:
        logging.error(f"Ошибка в обработке callback_query: {e}")
        try:
            await query.message.reply_text(
                "Произошла ошибка. Попробуйте снова /start",
                parse_mode='Markdown'
            )
        except:
            pass

async def choose_bot_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор уровня для игры с ботом"""
    query = update.callback_query
    user = query.from_user
    
    keyboard = []
    for level, info in WORD_DATABASE.items():
        if level != 7:  # Исключаем свободный режим
            if not is_level_unlocked(user.id, level):
                if level == 6:
                    keyboard.append([InlineKeyboardButton(f"🔒 {info['name']} (2 слова!) - {info['points']}⭐", callback_data="locked")])
                else:
                    keyboard.append([InlineKeyboardButton(f"🔒 {info['name']} - {info['points']}⭐", callback_data="locked")])
            else:
                available_words = get_available_words(user.id, level)
                if not available_words:
                    if level == 6:
                        keyboard.append([InlineKeyboardButton(f"✅ {info['name']} (ПРОЙДЕН!) - {info['points']}⭐", callback_data=f"bot_level_{level}")])
                    else:
                        keyboard.append([InlineKeyboardButton(f"✅ {info['name']} (ПРОЙДЕН!) - {info['points']}⭐", callback_data=f"bot_level_{level}")])
                else:
                    progress = get_user_progress(user.id, level)
                    guessed = len(progress['levels'].get(level, []))
                    total = len(WORD_DATABASE[level]['words'])
                    
                    if level == 6:
                        keyboard.append([InlineKeyboardButton(f"{info['name']} ({guessed}/{total}) - {info['points']}⭐", callback_data=f"bot_level_{level}")])
                    else:
                        keyboard.append([InlineKeyboardButton(f"{info['name']} ({guessed}/{total}) - {info['points']}⭐", callback_data=f"bot_level_{level}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    progress = get_user_progress(user.id)
    progress_text = f"📊 *Твой прогресс:* Уровень {progress['max_level']}/6\n"
    progress_text += f"🎯 Отгадано слов: {progress['total_words']}\n\n"
    
    await query.edit_message_text(
        progress_text + 
        "🤖 *Выбери уровень сложности для игры с ботом:*\n\n"
        "*Чем сложнее уровень - тем больше очков!*\n"
        "🔒 - уровень заблокирован (пройди предыдущий)\n"
        "✅ - уровень полностью пройден\n"
        "👑 *Легендарный уровень:* ДВА СЛОВА через пробел!\n\n"
        "*Чтобы открыть следующий уровень, нужно отгадать ВСЕ слова на текущем!*",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def choose_friend_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор уровня для игры с другом"""
    query = update.callback_query
    
    keyboard = [
        [InlineKeyboardButton("🎯 Свободный режим (загадываешь сам)", callback_data="friend_level_7")],
        [InlineKeyboardButton("🤖 Загадать слово из базы", callback_data="friend_bot_words")]
    ]
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "👥 *Игра с другом:*\n\n"
        "Выбери тип игры:\n"
        "🎯 *Свободный режим* - ты сам загадываешь любое слово\n"
        "🤖 *Из базы* - бот загадывает слово из выбранного уровня",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def choose_friend_bot_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор уровня для игры с другом (бот загадывает)"""
    query = update.callback_query
    user = query.from_user
    
    keyboard = []
    for level, info in WORD_DATABASE.items():
        if level != 7:
            if not is_level_unlocked(user.id, level):
                if level == 6:
                    keyboard.append([InlineKeyboardButton(f"🔒 {info['name']} (2 слова!)", callback_data="locked")])
                else:
                    keyboard.append([InlineKeyboardButton(f"🔒 {info['name']}", callback_data="locked")])
            else:
                if level == 6:
                    keyboard.append([InlineKeyboardButton(f"👑 {info['name']} (2 слова!)", callback_data=f"friend_bot_level_{level}")])
                else:
                    keyboard.append([InlineKeyboardButton(f"{info['name']}", callback_data=f"friend_bot_level_{level}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="play_with_friend")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🤖 *Выбери уровень сложности (бот загадает слово):*\n\n"
        "*Друг будет отгадывать слово из этого уровня*\n"
        "🔒 - уровень заблокирован для тебя\n"
        "👑 *Легендарный уровень:* ДВА СЛОВА через пробел!",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def start_bot_game(update: Update, context: ContextTypes.DEFAULT_TYPE, level: int):
    """Начинает игру с ботом (пользователь отгадывает)"""
    query = update.callback_query
    user = query.from_user
    user_id = user.id
    
    if not is_level_unlocked(user_id, level):
        await query.edit_message_text(
            f"❌ *Уровень заблокирован!*\n\n"
            f"Чтобы открыть уровень {WORD_DATABASE[level]['name']}, "
            f"нужно отгадать ВСЕ слова на предыдущих уровнях!\n\n"
            f"Вернись в меню и продолжай играть на доступных уровнях! 💪",
            parse_mode='Markdown'
        )
        return
    
    available_words = get_available_words(user_id, level)
    
    if not available_words:
        await query.edit_message_text(
            f"🎉 *Поздравляем! Ты полностью прошел уровень {WORD_DATABASE[level]['name']}!*\n\n"
            f"Все слова этого уровня отгаданы! 🏆\n\n"
            f"Попробуй другие уровни или проверь, не открылся ли следующий уровень!",
            parse_mode='Markdown'
        )
        return
    
    secret_word = random.choice(available_words)
    
    logging.info(f"🎮 Начата игра: {user.full_name} (ID: {user_id}) - Уровень {level}: {secret_word}")
    
    await notify_owner(context, f"🎮 *НОВАЯ ИГРА НАЧАТА!*\n\n"
                          f"Игрок: {user.full_name}\n"
                          f"ID: `{user_id}`\n"
                          f"Уровень: {WORD_DATABASE[level]['name']}\n"
                          f"Слово: ||{secret_word}||\n"
                          f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    
    user_games[user_id] = {
        'word': secret_word, 'guesses': [],
        'level': level,
        'game_type': 'bot',
        'start_time': datetime.now().isoformat()
    }
    
    if level == 6:
        level_message = (
            f"👑 *Легендарный уровень!*\n\n"
            f"Бот загадал *ДВА СЛОВА через пробел*\n"
            f"Пример: 'высоковольтный трансформатор'\n\n"
            f"📏 Длина слова: *{len(secret_word)}* букв\n"
            f"⭐ Очки за победу: {WORD_DATABASE[level]['points']}\n\n"
            f"*Пиши два слова через пробел!*\n"
            f"Отправь слово и начни отгадывать! 💪"
        )
    else:
        progress = get_user_progress(user_id, level)
        guessed = len(progress['levels'].get(level, []))
        total = len(WORD_DATABASE[level]['words'])
        
        level_message = (
            f"🤖 *Игра с ботом началась!*\n\n"
            f"📏 Уровень: {WORD_DATABASE[level]['name']}\n"
            f"📊 Прогресс: {guessed}/{total} слов\n"
            f"🔤 Бот загадал слово из *{len(secret_word)}* букв!\n"
            f"⭐ Очки за победу: {WORD_DATABASE[level]['points']}\n\n"
            f"*Подсказки:*\n"
            f"🟩 - буква на месте\n"
            f"🟨 - буква есть, но не там\n"
            f"⬜ - буквы нет\n\n"
            f"Отправь слово и начни отгадывать! 💪"
        )
    
    await query.edit_message_text(level_message, parse_mode='Markdown')

async def start_bot_game_for_friend(update: Update, context: ContextTypes.DEFAULT_TYPE, level: int):
    """Бот загадывает слово для игры с другом"""
    query = update.callback_query
    user = query.from_user
    user_id = user.id
    
    if not is_level_unlocked(user_id, level):
        await query.edit_message_text(
            f"❌ *Уровень заблокирован!*\n\n"
            f"Чтобы загадать слово из уровня {WORD_DATABASE[level]['name']}, "
            f"нужно отгадать ВСЕ слова на предыдущих уровнях!\n\n"
            f"Вернись в меню и продолжай играть на доступных уровнях! 💪",
            parse_mode='Markdown'
        )
        return
    
    level_info = WORD_DATABASE[level]
    available_words = [w for w in level_info['words'] if w not in used_words]
    
    if not available_words:
        await query.edit_message_text(
            f"❌ *Все слова уровня '{level_info['name']}' уже были отгаданы в других играх!*\n\n"
            "Попробуй другой уровень или свободный режим!",
            parse_mode='Markdown'
        )
        return
    
    secret_word = random.choice(available_words)
    
    logging.info(f"👥 Игра с другом создана: {user.full_name} (ID: {user_id}) - Уровень {level}")
    
    game_id = f"friend_{user_id}_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}"
    
    game_links[game_id] = {
        'creator_id': user_id,
        'creator_name': user.full_name,
        'word': secret_word,
        'level': level,
        'game_type': 'friend',
        'created_at': datetime.now().isoformat(),
        'players': []  # Список игроков, которые присоединились
    }
    
    active_games[game_id] = {
        'creator': user_id,
        'creator_name': user.full_name,
        'word': secret_word,
        'level': level,
        'game_type': 'friend',
        'players': []  # Список игроков, которые присоединились
    }
    
    bot_username = (await context.bot.get_me()).username
    share_url = f"https://t.me/{bot_username}?start={game_id}"
    
    save_data()
    
    await notify_owner(context, f"👥 *СОЗДАНА ИГРА С ДРУГОМ!*\n\n"
                          f"Создатель: {user.full_name}\n"
                          f"ID: `{user_id}`\n"
                          f"Уровень: {WORD_DATABASE[level]['name']}\n"
                          f"Слово: ||{secret_word}||\n"
                          f"Ссылка: `{share_url}`\n"
                          f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    
    keyboard = [[InlineKeyboardButton("🎮 Начать отгадывать", url=share_url)],
        [InlineKeyboardButton("🔙 Назад", callback_data="play_with_friend")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    level_name = WORD_DATABASE[level]["name"]
    points = WORD_DATABASE[level]["points"]
    
    if level == 6:
        word_display = f"*{secret_word.upper()}* (два слова)"
    else:
        word_display = f"*{secret_word.upper()}*"
    
    await query.edit_message_text(
        f"✅ *Бот загадал слово для друга!*\n\n"
        f"📏 Уровень: {level_name}\n"
        f"🔤 Слово: {word_display}\n"
        f"📏 Длина: *{len(secret_word)}* букв\n"
        f"⭐ Очки за победу: {points}\n\n"
        f"🔗 *Ссылка для друга:*\n`{share_url}`\n\n"
        f"Отправь эту ссылку другу! 📤\n"
        f"*Ты не можешь отгадать это слово сам!*",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def show_leaderboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает таблицу лидеров через callback"""
    query = update.callback_query
    
    if not leaderboard:
        await query.edit_message_text("📊 Таблица лидеров пока пуста! Сыграй первую игру!")
        return
    
    sorted_by_points = sorted(leaderboard.items(), key=lambda x: x[1]['total_points'], reverse=True)
    
    leaderboard_text = "🏆 *ТОП-10 ИГРОКОВ (все время):*\n\n"
    
    for i, (user_id, data) in enumerate(sorted_by_points[:10], 1):
        medal = ""
        if i == 1: medal = "🥇"
        elif i == 2: medal = "🥈"
        elif i == 3: medal = "🥉"
        else: medal = f"{i}."
        
        leaderboard_text += f"{medal} *{data['name']}*\n"
        leaderboard_text += f"   ⭐ Очков: {data['total_points']}\n"
        leaderboard_text += f"   🏅 Всего побед: {data['total_wins']}\n"
        leaderboard_text += f"   🤖 Побед с ботом: {data.get('bot_wins', 0)}\n"
        leaderboard_text += f"   👥 Побед с друзьями: {data.get('friend_wins', 0)}\n\n"
    
    if weekly_stats:
        sorted_weekly = sorted(weekly_stats.items(), key=lambda x: x[1]['points'], reverse=True)
        
        leaderboard_text += "📅 *НЕДЕЛЬНЫЙ ТОП-5:*\n\n"
        
        for i, (user_id, data) in enumerate(sorted_weekly[:5], 1):
            medal = ""
            if i == 1: medal = "🥇"
            elif i == 2: medal = "🥈"
            elif i == 3: medal = "🥉"
            else: medal = f"{i}."
            
            leaderboard_text += f"{medal} *{data['name']}* - {data['points']} очков ({data['games_won']} побед)\n"
        
        leaderboard_text += "\n🎁 *Недельные награды:*\n"
        leaderboard_text += "🥇 1 место: 500 очков + VIP статус\n"
        leaderboard_text += "🥈 2 место: 300 очков\n"
        leaderboard_text += "🥉 3 место: 150 очков\n\n"
        leaderboard_text += f"📢 *Чтобы получить награды, зайдите в канал:* @{CHANNEL_USERNAME}\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(leaderboard_text, parse_mode='Markdown', reply_markup=reply_markup)

async def show_my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает статистику пользователя"""
    query = update.callback_query
    user = query.from_user
    
    if user.id in user_stats:
        stats = user_stats[user.id]
        progress = get_user_progress(user.id)
        
        total_points = stats['total_points']
        if total_points >= 1000:
            rank = "👑 Легенда"
        elif total_points >= 500:
            rank = "💀 Мастер"
        elif total_points >= 200:
            rank = "🔥 Эксперт"
        elif total_points >= 100:
            rank = "🌲 Профессионал"
        elif total_points >= 50:
            rank = "🌿 Любитель"
        else:
            rank = "🍀 Начинающий"
        
        win_rate = (stats['games_won'] / stats['games_played'] * 100) if stats['games_played'] > 0 else 0
        
        stats_text = (
            f"📊 *Твоя статистика, {user.first_name}!*\n\n"
            f"🏆 Ранг: {rank}\n"
            f"⭐ Всего очков: {stats['total_points']}\n"
            f"🎮 Сыграно игр: {stats['games_played']}\n"
            f"🏅 Побед: {stats['games_won']}\n"
            f"📈 Процент побед: {win_rate:.1f}%\n"
            f"📖 Отгадано слов: {stats.get('words_guessed', 0)}\n\n"
            f"🤖 Игр с ботом: {stats.get('bot_games', 0)}\n"
            f"👥 Игр с друзьями: {stats.get('friend_games', 0)}\n\n"
            f"📅 Последняя игра: {stats['last_played'][:10]}\n\n"
            f"*Прогресс по уровням:*\n"
        )
        
        for level in range(1, 7):
            level_info = WORD_DATABASE[level]
            guessed = len(progress['levels'].get(level, []))
            total = len(level_info['words'])
            unlocked = is_level_unlocked(user.id, level)
            
            if not unlocked:
                stats_text += f"🔒 {level_info['name']}: заблокирован\n"
            elif guessed == total:
                stats_text += f"✅ {level_info['name']}: {guessed}/{total} (ПРОЙДЕН!)\n"
            else:
                stats_text += f"{level_info['name']}: {guessed}/{total}\n"
        
        stats_text += f"\n🎯 *Максимальный уровень:* {progress['max_level']}/6\n"
        
        if user.id in weekly_stats:
            weekly = weekly_stats[user.id]
            stats_text += f"\n*Недельная статистика:*\n"
            stats_text += f"⭐ Очков: {weekly['points']}\n"
            stats_text += f"🏅 Побед: {weekly['games_won']}\n"
            
            sorted_weekly = sorted(weekly_stats.items(), key=lambda x: x[1]['points'], reverse=True)
            position = next((i+1 for i, (uid, _) in enumerate(sorted_weekly) if uid == user.id), None)
            
            if position:
                stats_text += f"🏆 Позиция в топе: {position}\n"
                
                if position <= 3:
                    stats_text += f"\n🎁 *Ты в топ-3 этой недели!*\n"
                    if position == 1:
                        stats_text += "Награда: 500 очков + VIP статус!\n"
                    elif position == 2:
                        stats_text += "Награда: 300 очков!\n"
                    elif position == 3:
                        stats_text += "Награда: 150 очков!\n"
                    stats_text += f"Зайди в @{CHANNEL_USERNAME} для получения!"
        
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(stats_text, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📊 *У тебя еще нет статистики!*\n\n"
            "Сыграй свою первую игру, чтобы появилась статистика! 🎮",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

async def help_command_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает правила через callback"""
    query = update.callback_query
    
    help_text = """
🎯 *ПРАВИЛА ИГРЫ:*

*🤖 РЕЖИМЫ ИГРЫ:*

1. *Игра с ботом* - бот загадывает слово, ты отгадываешь
   • Выбираешь уровень сложности
   • Отгадываешь слово
   • Получаешь очки за победу

2. *Игра с другом* - ты загадываешь слово другу
   • Свободный режим: загадываешь любое слово
   • Из базы: бот загадывает слово из уровня
   • Отправляешь ссылку другу

*📊 СИСТЕМА ПРОГРЕССА:*
🔒 *Уровни блокируются!*
Чтобы открыть следующий уровень, нужно отгадать ВСЕ слова на текущем!
Пример: Чтобы играть на уровне 2, нужно отгадать все слова уровня 1.

*📊 УРОВНИ СЛОЖНОСТИ:*
🍀 Начинающий (3-4 буквы, 10 очков)
🌿 Любитель (5-6 букв, 25 очков)
🌲 Профессионал (7-8 букв, 50 очков)
🔥 Эксперт (9-10 букв, 100 очков)
💀 Мастер (11-15 букв, 200 очков)
👑 Легенда (16+ букв, ДВА СЛОВА, 500 очков)
🎯 Свободный режим (любое слово, 0 очков)

*⚠️ ВАЖНО:* В легендарном уровне используй ДВА СЛОВА через пробел!

*🎯 ПОДСКАЗКИ:*
🟩 - буква на правильном месте
🟨 - буква есть в слове, но не на своем месте
⬜ - буквы нет в слове

*🎁 СИСТЕМА НАГРАД:*
🏆 *Недельные призы:*
🥇 1 место: 500 очков + VIP статус
🥈 2 место: 300 очков
🥉 3 место: 150 очков

📅 Неделя сбрасывается каждое воскресенье в 15:00 по МСК
📢 Награды получаем в канале: @""" + CHANNEL_USERNAME + """

*⚡ СОВЕТЫ:*
• Начинай с гласных букв
• Запоминай желтые буквы
• Используй разные комбинации
• Следи за таблицей лидеров!
"""
    
    keyboard = [
        [InlineKeyboardButton("🎮 Начать игру", callback_data="play_with_bot")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(help_text, parse_mode='Markdown', reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает правила через команду"""
    help_text = """
🎯 *ПРАВИЛА ИГРЫ:*

*🤖 РЕЖИМЫ ИГРЫ:*

1. *Игра с ботом* - бот загадывает слово, ты отгадываешь
   • Выбираешь уровень сложности
   • Отгадываешь слово
   • Получаешь очки за победу

2. *Игра с другом* - ты загадываешь слово другу
   • Свободный режим: загадываешь любое слово
   • Из базы: бот загадывает слово из уровня
   • Отправляешь ссылку другу

*📊 СИСТЕМА ПРОГРЕССА:*
🔒 *Уровни блокируются!*
Чтобы открыть следующий уровень, нужно отгадать ВСЕ слова на текущем!
Пример: Чтобы играть на уровне 2, нужно отгадать все слова уровня 1.

*📊 УРОВНИ СЛОЖНОСТИ:*
🍀 Начинающий (3-4 буквы, 10 очков)
🌿 Любитель (5-6 букв, 25 очков)
🌲 Профессионал (7-8 букв, 50 очков)
🔥 Эксперт (9-10 букв, 100 очков)
💀 Мастер (11-15 букв, 200 очков)
👑 Легенда (16+ букв, ДВА СЛОВА, 500 очков)
🎯 Свободный режим (любое слово, 0 очков)

*⚠️ ВАЖНО:* В легендарном уровне используй ДВА СЛОВА через пробел!

*🎯 ПОДСКАЗКИ:*
🟩 - буква на правильном месте
🟨 - буква есть в слове, но не на своем месте
⬜ - буквы нет в слове

*🎁 СИСТЕМА НАГРАД:*
🏆 *Недельные призы:*
🥇 1 место: 500 очков + VIP статус
🥈 2 место: 300 очков
🥉 3 место: 150 очков

📅 Неделя сбрасывается каждое воскресенье в 15:00 по МСК
📢 Награды получаем в канале: @""" + CHANNEL_USERNAME + """

*⚡ СОВЕТЫ:*
• Начинай с гласных букв
• Запоминай желтые буквы
• Используй разные комбинации
• Следи за таблицей лидеров!
"""
    
    keyboard = [
        [InlineKeyboardButton("🎮 Начать игру", callback_data="play_with_bot")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(help_text, parse_mode='Markdown', reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает текстовые сообщения"""
    user = update.effective_user
    
    logging.info(f"💬 Сообщение от {user.full_name} (ID: {user.id}): {update.message.text[:50]}...")
    
    user_id = user.id
    text = update.message.text.strip().lower()
    
    if user_id in waiting_for_word:
        await process_friend_word_input(update, context, text)
        return
    
    if user_id in user_games:
        await process_guess(update, context, text)
        return
    
    keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Напиши /start для начала игры!\n"
        "Или перейди по ссылке от друга! 🔗",
        reply_markup=reply_markup
    )

async def process_friend_word_input(update: Update, context: ContextTypes.DEFAULT_TYPE, word: str):
    """Обрабатывает ввод слова для свободного режима"""
    user_id = update.effective_user.id
    
    level = waiting_for_level.get(user_id, 7)
    level_info = WORD_DATABASE[level]
    
    if len(word) < level_info["min_length"] or len(word) > level_info["max_length"]:
        await update.message.reply_text(f"❌ Слово должно быть {level_info['min_length']}-{level_info['max_length']} букв! Твое: {len(word)} букв.")
        return
    
    if not re.match('^[а-яё ]+$', word):
        await update.message.reply_text("❌ Используй только русские буквы и пробелы!")
        return
    
    if word in used_words:
        await update.message.reply_text("❌ Это слово уже было отгадано в другой игре! Выбери другое слово.")
        return
    
    game_id = f"free_{user_id}_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}"
    
    game_links[game_id] = {
        'creator_id': user_id,
        'creator_name': update.effective_user.full_name,
        'word': word,
        'level': level,
        'game_type': 'friend',
        'created_at': datetime.now().isoformat(),
        'players': []
    }
    
    active_games[game_id] = {
        'creator': user_id,
        'creator_name': update.effective_user.full_name,
        'word': word,
        'level': level,
        'game_type': 'friend',
        'players': []
    }
    
    del waiting_for_word[user_id]
    del waiting_for_level[user_id]
    
    logging.info(f"👥 Создана игра в свободном режиме: {update.effective_user.full_name} - Слово: {word}")
    
    bot_username = (await context.bot.get_me()).username
    share_url = f"https://t.me/{bot_username}?start={game_id}"
    
    save_data()
    
    await notify_owner(context, f"🎯 *СОЗДАНА ИГРА В СВОБОДНОМ РЕЖИМЕ!*\n\n"
                          f"Создатель: {update.effective_user.full_name}\n"
                          f"ID: `{user_id}`\n"
                          f"Слово: ||{word}||\n"
                          f"Ссылка: `{share_url}`\n"
                          f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    
    keyboard = [
        [InlineKeyboardButton("🎮 Начать отгадывать", url=share_url)],
        [InlineKeyboardButton("🔙 Назад", callback_data="play_with_friend")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ *Отлично! Ты загадал слово!*\n\n"
        f"🔤 Слово: *{word.upper()}*\n"
        f"📏 Длина: *{len(word)}* букв\n"
        f"🎯 Режим: Свободный (без очков)\n\n"
        f"🔗 *Ссылка для друга:*\n`{share_url}`\n\n"
        f"Отправь эту ссылку другу! 📤\n"
        f"*Ты не можешь отгадать свое же слово!*",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def notify_game_creator(game_id: str, winner_id: int, winner_name: str, word: str, attempts: int, context: ContextTypes.DEFAULT_TYPE):
    """Уведомляет создателя игры, что его слово отгадали"""
    if game_id in game_links:
        game_info = game_links[game_id]
        creator_id = game_info['creator_id']
        
        if creator_id != winner_id:  # Не уведомляем, если создатель сам отгадал
            try:
                level_name = WORD_DATABASE[game_info['level']]['name'] if game_info['level'] != 7 else "Свободный режим"
                
                await context.bot.send_message(
                    creator_id,
                    f"🎉 *Твое слово отгадали!*\n\n"
                    f"👤 Отгадал: {winner_name}\n"
                    f"📏 Уровень: {level_name}\n"
                    f"🔤 Слово: *{word.upper()}*\n"
                    f"📊 Попыток: {attempts}\n\n"
                    f"*Игра завершена! Ссылка больше не активна.*",
                    parse_mode='Markdown'
                )
                logging.info(f"Уведомление отправлено создателю игры {creator_id}")
            except Exception as e:
                logging.error(f"Не удалось отправить уведомление создателю {creator_id}: {e}")

async def process_guess(update: Update, context: ContextTypes.DEFAULT_TYPE, guess: str):
    """Обрабатывает попытку отгадать слово"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    if user_id not in user_games:
        await update.message.reply_text("❌ У тебя нет активной игры!")
        return
    
    game_data = user_games[user_id]
    secret_word = game_data['word']
    guess = guess.lower()
    
    logging.info(f"🎯 Попытка от {user_name}: {guess} (слово: {secret_word})")
    
    guess_clean = guess.strip()
    secret_clean = secret_word.strip()
    
    if len(guess_clean) != len(secret_clean):
        await update.message.reply_text(f"❌ Слово должно содержать {len(secret_clean)} букв! Твое: {len(guess_clean)} букв.")
        return
    
    if not re.match('^[а-яё ]+$', guess_clean):
        await update.message.reply_text("❌ Используй только русские буквы и пробелы!")
        return
    
    result = check_word(secret_clean, guess_clean)
    game_data['guesses'].append((guess_clean, result))
    
    if guess_clean == secret_clean:
        level = game_data['level']
        game_type = game_data.get('game_type', 'bot')
        game_id = game_data.get('game_id')
        
        # Обновляем прогресс и статистику
        if game_type == 'bot':
            new_word_added = update_user_progress(user_id, level, secret_word)
            points = WORD_DATABASE[level]["points"]
            await update_leaderboard(user_id, user_name, points, game_type)
        else:
            points = WORD_DATABASE[level]["points"] if level != 7 else 0
            if points > 0:
                await update_leaderboard(user_id, user_name, points, game_type)
            new_word_added = False
        
        attempts = len(game_data['guesses'])
        secret_word_display = secret_word.upper()
        if level == 6:
            secret_word_display += " (два слова)"
        
        response = f"🎉 *ПОЗДРАВЛЯЮ! Ты угадал!*\n\n"
        
        if game_type == 'bot':
            response += f"🤖 *Игра с ботом*\n"
            response += f"📏 Уровень: {WORD_DATABASE[level]['name']}\n"
            response += f"⭐ Твои очки: {points}\n"
            
            progress = get_user_progress(user_id)
            if new_word_added:
                guessed = len(progress['levels'].get(level, []))
                total = len(WORD_DATABASE[level]['words'])
                
                if guessed == total and level < 6:
                    response += f"\n🚀 *ПОЗДРАВЛЯЕМ! Ты прошел уровень полностью!*\n"
                    response += f"Открывается уровень {level + 1}!\n\n"
        else:
            response += f"👥 *Игра с другом*\n"
            if points > 0:
                response += f"📏 Уровень: {WORD_DATABASE[level]['name']}\n"
                response += f"⭐ Твои очки: {points}\n"
            else:
                response += f"🎯 Свободный режим (без очков)\n"
        
        response += f"🏆 Слово: *{secret_word_display}*\n"
        response += f"📊 Попыток: {attempts}\n\n"
        response += "📋 История попыток:\n"
        
        for i, (attempt, res) in enumerate(game_data['guesses'], 1):
            response += f"{i}. {attempt.upper()}: {res}\n"
        
        # Удаляем игру из активных
        if user_id in user_games:
            del user_games[user_id]
        
        # Удаляем активную игру, если это игра с другом
        if game_id and game_id in active_games:
            # Уведомляем создателя игры
            await notify_game_creator(game_id, user_id, user_name, secret_word, attempts, context)
            
            # Удаляем игру из активных
            del active_games[game_id]
            if game_id in game_links:
                del game_links[game_id]
            
            logging.info(f"Игра {game_id} удалена из активных")
        
        save_data()
        
        await notify_owner(context, f"🎉 *ИГРА ЗАВЕРШЕНА УСПЕШНО!*\n\n"
                              f"Игрок: {user_name}\n"
                              f"ID: `{user_id}`\n"
                              f"Слово: ||{secret_word}||\n"
                              f"Попыток: {attempts}\n"
                              f"Очки: {points}\n"
                              f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        
        keyboard = [
            [InlineKeyboardButton("🎮 Новая игра", callback_data="play_with_bot")],
            [InlineKeyboardButton("📊 Таблица лидеров", callback_data="leaderboard")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(response, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        attempts = len(game_data['guesses'])
        response = f"Попытка {attempts}:\n"
        response += f"🔤 {guess_clean.upper()}: {result}\n\n"
        
        if attempts > 1:
            response += "📋 Последние попытки:\n"
            for i, (attempt, res) in enumerate(game_data['guesses'][-3:], 1):
                response += f"{attempts-3+i}. {attempt.upper()}: {res}\n"
        
        if attempts >= 10:
            secret_word_display = secret_word.upper()
            if game_data['level'] == 6:
                secret_word_display += " (два слова)"
            
            game_type = game_data.get('game_type', 'bot')
            game_id = game_data.get('game_id')
            
            response = f"😔 *Не удалось отгадать...*\n\n"
            
            if game_type == 'bot':
                response += f"🤖 *Игра с ботом*\n"
                response += f"📏 Уровень: {WORD_DATABASE[game_data['level']]['name']}\n"
            else:
                response += f"👥 *Игра с другом*\n"
            
            response += f"Загаданное слово: *{secret_word_display}*\n\n"
            response += "Твои попытки:\n"
            for i, (attempt, res) in enumerate(game_data['guesses'], 1):
                response += f"{i}. {attempt.upper()}: {res}\n"
            
            if user_id in user_games:
                del user_games[user_id]
            
            # Удаляем активную игру, если это игра с другом
            if game_id and game_id in active_games:
                del active_games[game_id]
                if game_id in game_links:
                    del game_links[game_id]
            
            save_data()
            
            await notify_owner(context, f"❌ *ИГРА ПРОИГРАНА!*\n\n"
                                  f"Игрок: {user_name}\n"
                                  f"ID: `{user_id}`\n"
                                  f"Слово: ||{secret_word}||\n"
                                  f"Попыток: {attempts}/10\n"
                                  f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
            
            keyboard = [
                [InlineKeyboardButton("🎮 Новая игра", callback_data="play_with_bot")],
                [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(response, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            response += f"\n💡 Попробуй ещё! Осталось попыток: {10 - attempts}"
            await update.message.reply_text(response)

def check_word(secret_word, guess):
    """Проверяет guess и возвращает результат в виде смайликов"""
    secret = list(secret_word)
    guess_list = list(guess)
    result = ['⬜'] * len(secret_word)
    
    for i in range(len(secret_word)):
        if guess_list[i] == secret[i]:
            result[i] = '🟩'
            secret[i] = None
            guess_list[i] = None
    
    for i in range(len(secret_word)):
        if guess_list[i] is not None and guess_list[i] in secret:
            result[i] = '🟨'
            secret[secret.index(guess_list[i])] = None
    
    return ''.join(result)

async def handle_start_with_params(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик старта с параметрами (по ссылке)"""
    user = update.effective_user
    
    logging.info(f"🔗 Переход по ссылке от {user.full_name} (ID: {user.id})")
    
    if context.args:
        game_id = context.args[0]
        
        # ПРОВЕРЯЕМ ПОДПИСКУ ДЛЯ ИГРОКОВ ПО ССЫЛКЕ
        if not await check_subscription(user.id, context):
            await show_subscription_required(update, context)
            return
        
        if game_id in game_links:
            game_info = game_links[game_id]
            creator_id = game_info['creator_id']
            creator_name = game_info.get('creator_name', 'Неизвестный')
            
            logging.info(f"🎮 Подключение к игре: {user.full_name} -> игра от {creator_name} (ID: {creator_id})")
            
            await notify_owner(context, f"🔗 *ПОДКЛЮЧЕНИЕ К ИГРЕ!*\n\n"
                                  f"Игрок: {user.full_name}\n"
                                  f"ID: `{user.id}`\n"
                                  f"Подключился к игре от: {creator_name}\n"
                                  f"Слово: ||{game_info['word']}||\n"
                                  f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
            
            if user.id == creator_id:
                keyboard = [[InlineKeyboardButton("🎮 Загадать новое слово", callback_data="play_with_friend")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "❌ *Ты не можешь отгадывать свое же слово!*\n\n"
                    "Отправь эту ссылку другу, а сам загадай новое слово! 🎮",
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                return
            
            if game_id not in active_games:
                keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "❌ *Эта игра уже завершена!*\n\n"
                    "Слово было отгадано. Попроси друга отправить тебе новую ссылку! 🔗",
                    reply_markup=reply_markup
                )
                return
            
            secret_word = game_info['word']
            level = game_info['level']
            game_type = game_info['game_type']
            
            user_games[user.id] = {
                'word': secret_word,
                'guesses': [],
                'level': level,
                'game_type': game_type,
                'game_id': game_id
            }
            
            if game_type == 'bot':
                game_type_text = "🤖 Бот загадал слово"
            else:
                game_type_text = "👥 Друг загадал слово"
            
            if level == 6:
                level_message = (
                    f"{game_type_text}\n\n"
                    f"👑 *Легендарный уровень!*\n"
                    f"Тебе загадали *ДВА СЛОВА через пробел*\n"
                    f"Пример: 'высоковольтный трансформатор'\n\n"
                    f"📏 Длина слова: *{len(secret_word)}* букв\n"
                    f"⭐ Очки за победу: {WORD_DATABASE[level]['points'] if level != 7 else 0}\n\n"
                    f"*Пиши два слова через пробел!*\n"
                    f"Отправь слово и начни отгадывать! 💪"
                )
            else:
                points_text = f"⭐ Очки за победу: {WORD_DATABASE[level]['points']}" if level != 7 else "🎯 Свободный режим (без очков)"
                
                level_message = (
                    f"{game_type_text}\n\n"
                    f"📏 Уровень: {WORD_DATABASE[level]['name']}\n"
                    f"🔤 Слово из *{len(secret_word)}* букв!\n"
                    f"{points_text}\n\n"
                    f"*Подсказки:*\n"
                    f"🟩 - буква на месте\n"
                    f"🟨 - буква есть, но не там\n"
                    f"⬜ - буквы нет\n\n"
                    f"Отправь слово и начни отгадывать! 💪"
                )
            
            await update.message.reply_text(level_message, parse_mode='Markdown')
            return
        else:
            keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "❌ *Ссылка недействительна!*\n\n"
                "Возможно, игра уже завершена или ссылка устарела.\n"
                "Попроси друга отправить новую ссылку! 🔗",
                reply_markup=reply_markup
            )
            return
    
    await start(update, context)

def calculate_next_sunday_15_00():
    """Вычисляет время следующего воскресенья 15:00"""
    now = datetime.now()
    
    days_until_sunday = (6 - now.weekday()) % 7
    if days_until_sunday == 0 and now.hour >= 15:
        days_until_sunday = 7
    
    next_sunday = now + timedelta(days=days_until_sunday)
    next_sunday = next_sunday.replace(hour=15, minute=0, second=0, microsecond=0)
    
    return next_sunday

async def handle_locked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик для заблокированных кнопок"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🔒 *Уровень заблокирован!*\n\n"
        "Чтобы открыть этот уровень, нужно отгадать ВСЕ слова на предыдущих уровнях!\n\n"
        "Продолжай играть на доступных уровнях! 💪",
        parse_mode='Markdown'
    )

def main():
    """Главная функция запуска бота"""
    load_data()
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    job_queue = application.job_queue
    
    if job_queue:
        next_reset = calculate_next_sunday_15_00()
        delay = (next_reset - datetime.now()).total_seconds()
        
        if delay < 0:
            delay = 0
        
        job_queue.run_once(reset_weekly_stats, delay)
        job_queue.run_repeating(reset_weekly_stats, interval=604800, first=delay)
        
        logging.info(f"Планировщик задач настроен. Следующий сброс через {delay/3600:.1f} часов")
    else:
        logging.warning("JobQueue не доступен. Автоматический сброс статистики не будет работать!")
    
    application.add_handler(CommandHandler("start", handle_start_with_params))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("leaderboard", show_leaderboard))
    application.add_handler(CommandHandler("stats", show_my_stats))
    application.add_handler(CommandHandler("reset_weekly", manual_weekly_reset_command))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    application.add_handler(CallbackQueryHandler(handle_locked, pattern="^locked$"))
    
    print("🎮 Игровой бот запущен!")
    print(f"👉 Используйте /start для начала")
    print(f"📢 Канал: @{CHANNEL_USERNAME}")
    print(f"🤖 Режимы: игра с ботом / игра с другом")
    print(f"📊 Игроков в базе: {len(leaderboard)}")
    print(f"🎯 Система прогресса: нужно отгадать все слова на уровне для открытия следующего!")
    print(f"📝 Логи сохраняются в файл: bot_activity.log")
    print(f"🔔 Уведомления владельца включены!")
    print(f"⚠️ Проверка подписки: РАБОТАЕТ ДЛЯ ВСЕХ ИГРОКОВ (включая переход по ссылке)")
    print(f"🔄 Сброс статистики: каждое воскресенье 15:00 МСК")
    print(f"⚙️  Ручной сброс: /reset_weekly (только для владельца)")
    print(f"📁 Данные сохраняются в папке: {DATA_FOLDER}/")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
