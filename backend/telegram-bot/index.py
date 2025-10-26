'''
Business: Telegram bot для управления подписками и рассылки открыток через webhook
Args: event - dict with httpMethod, body (Telegram webhook updates)
      context - object with attributes: request_id, function_name
Returns: HTTP response dict
'''

import json
import os
from typing import Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import urllib.request
import urllib.parse

def get_db_connection():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def send_telegram_message(bot_token: str, chat_id: int, text: str, reply_markup: Optional[Dict] = None) -> bool:
    api_url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    params = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    
    if reply_markup:
        params['reply_markup'] = json.dumps(reply_markup)
    
    try:
        data_encoded = urllib.parse.urlencode(params).encode('utf-8')
        req = urllib.request.Request(api_url, data=data_encoded)
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get('ok', False)
    except Exception as e:
        print(f'Failed to send message: {str(e)}')
        return False

def send_telegram_photo(bot_token: str, chat_id: int, photo_url: str, caption: str = '') -> bool:
    api_url = f'https://api.telegram.org/bot{bot_token}/sendPhoto'
    params = {
        'chat_id': chat_id,
        'photo': photo_url,
        'caption': caption,
        'parse_mode': 'HTML'
    }
    
    try:
        data_encoded = urllib.parse.urlencode(params).encode('utf-8')
        req = urllib.request.Request(api_url, data=data_encoded)
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get('ok', False)
    except Exception as e:
        print(f'Failed to send photo: {str(e)}')
        return False

def answer_callback_query(bot_token: str, callback_query_id: str, text: str, show_alert: bool = False) -> bool:
    api_url = f'https://api.telegram.org/bot{bot_token}/answerCallbackQuery'
    params = {
        'callback_query_id': callback_query_id,
        'text': text,
        'show_alert': show_alert
    }
    
    try:
        data_encoded = urllib.parse.urlencode(params).encode('utf-8')
        req = urllib.request.Request(api_url, data=data_encoded)
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get('ok', False)
    except Exception:
        return False

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method: str = event.get('httpMethod', 'POST')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'TELEGRAM_BOT_TOKEN not configured'}),
            'isBase64Encoded': False
        }
    
    if method == 'POST':
        body_data = json.loads(event.get('body', '{}'))
        
        if 'message' in body_data:
            return handle_message(body_data['message'], bot_token)
        elif 'callback_query' in body_data:
            return handle_callback_query(body_data['callback_query'], bot_token)
        elif 'action' in body_data:
            return handle_api_action(body_data, bot_token)
    
    if method == 'GET':
        return get_subscribers_count()
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'ok': True}),
        'isBase64Encoded': False
    }

def handle_message(message: Dict[str, Any], bot_token: str) -> Dict[str, Any]:
    chat_id = message['chat']['id']
    text = message.get('text', '')
    username = message['from'].get('username', '')
    first_name = message['from'].get('first_name', '')
    
    if text == '/start':
        welcome_text = (
            f"🌸 Добро пожаловать, <b>{first_name}</b>!\n\n"
            "Я бот для ежедневной рассылки красивых открыток с пожеланиями.\n\n"
            "Каждый день вы будете получать:\n"
            "🌅 Открытку с добрым утром\n"
            "🎉 Праздничные поздравления\n"
            "💝 Теплые слова и пожелания\n\n"
            "Нажмите кнопку ниже, чтобы подписаться!"
        )
        
        keyboard = {
            'inline_keyboard': [[
                {'text': '✨ Подписаться на открытки', 'callback_data': 'subscribe'}
            ]]
        }
        
        send_telegram_message(bot_token, chat_id, welcome_text, keyboard)
    
    elif text == '/help':
        help_text = (
            "📖 <b>Как пользоваться ботом:</b>\n\n"
            "/start - Начать работу с ботом\n"
            "/subscribe - Подписаться на рассылку\n"
            "/unsubscribe - Отписаться от рассылки\n"
            "/status - Проверить статус подписки\n"
            "/help - Показать эту справку"
        )
        send_telegram_message(bot_token, chat_id, help_text)
    
    elif text == '/subscribe':
        subscribe_user_db(chat_id, username, first_name)
        success_text = (
            "✅ <b>Подписка активирована!</b>\n\n"
            "Теперь вы будете получать красивые открытки каждый день! 💌\n\n"
            "Чтобы отписаться, используйте команду /unsubscribe"
        )
        send_telegram_message(bot_token, chat_id, success_text)
    
    elif text == '/unsubscribe':
        unsubscribe_user_db(chat_id)
        goodbye_text = (
            "😢 <b>Подписка отменена</b>\n\n"
            "Мы будем скучать! Если передумаете, напишите /subscribe"
        )
        send_telegram_message(bot_token, chat_id, goodbye_text)
    
    elif text == '/status':
        is_subscribed = check_subscription_status(chat_id)
        if is_subscribed:
            status_text = "✅ <b>Ваша подписка активна!</b>\n\nВы получаете открытки каждый день 🎉"
        else:
            status_text = "❌ <b>Вы не подписаны</b>\n\nИспользуйте /subscribe для подписки"
        send_telegram_message(bot_token, chat_id, status_text)
    
    else:
        default_text = (
            "Я не понимаю эту команду 😕\n\n"
            "Используйте /help для списка доступных команд"
        )
        send_telegram_message(bot_token, chat_id, default_text)
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'ok': True}),
        'isBase64Encoded': False
    }

def handle_callback_query(callback_query: Dict[str, Any], bot_token: str) -> Dict[str, Any]:
    callback_id = callback_query['id']
    chat_id = callback_query['message']['chat']['id']
    data = callback_query['data']
    username = callback_query['from'].get('username', '')
    first_name = callback_query['from'].get('first_name', '')
    
    if data == 'subscribe':
        subscribe_user_db(chat_id, username, first_name)
        answer_callback_query(bot_token, callback_id, '✅ Подписка оформлена!')
        
        success_text = (
            "✅ <b>Отлично! Подписка активирована!</b>\n\n"
            "🌸 Теперь вы будете получать красивые открытки каждый день!\n\n"
            "💌 Первая открытка придет уже завтра утром\n\n"
            "Чтобы отписаться в любой момент, используйте /unsubscribe"
        )
        send_telegram_message(bot_token, chat_id, success_text)
    
    elif data == 'unsubscribe':
        unsubscribe_user_db(chat_id)
        answer_callback_query(bot_token, callback_id, '😢 Подписка отменена')
        
        goodbye_text = (
            "😢 <b>Подписка отменена</b>\n\n"
            "Мы будем скучать! Если передумаете, напишите /subscribe"
        )
        send_telegram_message(bot_token, chat_id, goodbye_text)
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'ok': True}),
        'isBase64Encoded': False
    }

def subscribe_user_db(chat_id: int, username: str, first_name: str):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        INSERT INTO telegram_subscribers (chat_id, username, first_name, is_active)
        VALUES (%s, %s, %s, true)
        ON CONFLICT (chat_id) 
        DO UPDATE SET is_active = true, username = EXCLUDED.username, first_name = EXCLUDED.first_name
    ''', (chat_id, username, first_name))
    
    conn.commit()
    cur.close()
    conn.close()

def unsubscribe_user_db(chat_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('UPDATE telegram_subscribers SET is_active = false WHERE chat_id = %s', (chat_id,))
    conn.commit()
    cur.close()
    conn.close()

def check_subscription_status(chat_id: int) -> bool:
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT is_active FROM telegram_subscribers WHERE chat_id = %s', (chat_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result and result['is_active']

def handle_api_action(data: Dict[str, Any], bot_token: str) -> Dict[str, Any]:
    action = data.get('action')
    
    if action == 'send_daily_cards':
        return send_daily_cards(bot_token)
    
    return {
        'statusCode': 400,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'error': 'Unknown action'}),
        'isBase64Encoded': False
    }

def send_daily_cards(bot_token: str) -> Dict[str, Any]:
    from datetime import datetime
    
    today = datetime.now()
    date_str = f"{str(today.month).zfill(2)}-{str(today.day).zfill(2)}"
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute('SELECT * FROM daily_cards WHERE date = %s', (date_str,))
    card = cur.fetchone()
    
    if not card:
        cur.close()
        conn.close()
        return {
            'statusCode': 404,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'No card for today'}),
            'isBase64Encoded': False
        }
    
    cur.execute('SELECT chat_id FROM telegram_subscribers WHERE is_active = true')
    subscribers = cur.fetchall()
    
    sent_count = 0
    failed_count = 0
    
    caption = f"<b>{card['title']}</b>\n\n{card['message']}"
    if card['is_holiday'] and card['holiday_name']:
        caption = f"🎉 <b>{card['holiday_name']}</b> 🎉\n\n{card['message']}"
    
    for subscriber in subscribers:
        chat_id = subscriber['chat_id']
        
        if send_telegram_photo(bot_token, chat_id, card['image_url'], caption):
            sent_count += 1
            cur.execute(
                'UPDATE telegram_subscribers SET last_sent_at = CURRENT_TIMESTAMP WHERE chat_id = %s',
                (chat_id,)
            )
        else:
            failed_count += 1
    
    conn.commit()
    cur.close()
    conn.close()
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'success': True,
            'sent_count': sent_count,
            'failed_count': failed_count,
            'card_title': card['title']
        }),
        'isBase64Encoded': False
    }

def get_subscribers_count() -> Dict[str, Any]:
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT COUNT(*) as count FROM telegram_subscribers WHERE is_active = true')
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'count': result['count']}),
        'isBase64Encoded': False
    }
