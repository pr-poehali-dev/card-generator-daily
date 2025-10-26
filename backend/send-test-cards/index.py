'''
Business: Отправка тестовых открыток подписчикам за несколько дней
Args: event - dict with httpMethod, body (количество дней)
      context - object with attributes: request_id
Returns: HTTP response dict
'''

import json
import os
from typing import Dict, Any, List
import psycopg2
from psycopg2.extras import RealDictCursor
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

def get_db_connection():
    return psycopg2.connect(os.environ['DATABASE_URL'])

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

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method: str = event.get('httpMethod', 'POST')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
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
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'TELEGRAM_BOT_TOKEN not configured'}),
            'isBase64Encoded': False
        }
    
    if method != 'POST':
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Method not allowed'}),
            'isBase64Encoded': False
        }
    
    body_data = json.loads(event.get('body', '{}'))
    days = body_data.get('days', 3)
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    today = datetime.now()
    dates_to_send = []
    
    for i in range(days):
        date = today - timedelta(days=i)
        date_str = f"{str(date.month).zfill(2)}-{str(date.day).zfill(2)}"
        dates_to_send.append(date_str)
    
    cur.execute('SELECT chat_id FROM telegram_subscribers WHERE is_active = true')
    subscribers = cur.fetchall()
    
    if not subscribers:
        cur.close()
        conn.close()
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': True,
                'message': 'Нет активных подписчиков',
                'sent_count': 0
            }),
            'isBase64Encoded': False
        }
    
    total_sent = 0
    total_failed = 0
    cards_sent = []
    
    for date_str in dates_to_send:
        cur.execute('SELECT * FROM cards WHERE date = %s', (date_str,))
        card = cur.fetchone()
        
        if not card:
            continue
        
        caption = f"<b>{card['title']}</b>\n\n{card['message']}"
        if card['is_holiday'] and card['holiday_name']:
            caption = f"🎉 <b>{card['holiday_name']}</b> 🎉\n\n{card['message']}"
        
        for subscriber in subscribers:
            chat_id = subscriber['chat_id']
            
            if send_telegram_photo(bot_token, chat_id, card['image_url'], caption):
                total_sent += 1
            else:
                total_failed += 1
        
        cards_sent.append({
            'date': date_str,
            'title': card['title'],
            'is_holiday': card['is_holiday']
        })
    
    cur.close()
    conn.close()
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({
            'success': True,
            'sent_count': total_sent,
            'failed_count': total_failed,
            'subscribers_count': len(subscribers),
            'cards_sent': cards_sent,
            'message': f'Отправлено {total_sent} открыток ({len(cards_sent)} дней) для {len(subscribers)} подписчиков'
        }),
        'isBase64Encoded': False
    }