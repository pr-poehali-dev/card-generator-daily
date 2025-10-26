'''
Business: Telegram bot для управления подписками и рассылки открыток
Args: event - dict with httpMethod, body, queryStringParameters
      context - object with attributes: request_id, function_name
Returns: HTTP response dict
'''

import json
import os
from typing import Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    return psycopg2.connect(os.environ['DATABASE_URL'])

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
    
    if method == 'POST':
        body_data = json.loads(event.get('body', '{}'))
        action = body_data.get('action')
        
        if action == 'subscribe':
            return subscribe_user(body_data)
        elif action == 'unsubscribe':
            return unsubscribe_user(body_data)
        elif action == 'send_card':
            return send_card_to_subscribers(body_data)
        
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Unknown action'}),
            'isBase64Encoded': False
        }
    
    if method == 'GET':
        return get_subscribers_count()
    
    return {
        'statusCode': 405,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'error': 'Method not allowed'}),
        'isBase64Encoded': False
    }

def subscribe_user(data: Dict[str, Any]) -> Dict[str, Any]:
    chat_id = data.get('chat_id')
    username = data.get('username', '')
    first_name = data.get('first_name', '')
    
    if not chat_id:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'chat_id is required'}),
            'isBase64Encoded': False
        }
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute('''
        INSERT INTO telegram_subscribers (chat_id, username, first_name, is_active)
        VALUES (%s, %s, %s, true)
        ON CONFLICT (chat_id) 
        DO UPDATE SET is_active = true, username = EXCLUDED.username, first_name = EXCLUDED.first_name
        RETURNING id
    ''', (chat_id, username, first_name))
    
    result = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({
            'success': True,
            'message': 'Подписка оформлена!',
            'subscriber_id': result['id']
        }),
        'isBase64Encoded': False
    }

def unsubscribe_user(data: Dict[str, Any]) -> Dict[str, Any]:
    chat_id = data.get('chat_id')
    
    if not chat_id:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'chat_id is required'}),
            'isBase64Encoded': False
        }
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('UPDATE telegram_subscribers SET is_active = false WHERE chat_id = %s', (chat_id,))
    conn.commit()
    cur.close()
    conn.close()
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'success': True, 'message': 'Подписка отменена'}),
        'isBase64Encoded': False
    }

def send_card_to_subscribers(data: Dict[str, Any]) -> Dict[str, Any]:
    import urllib.request
    import urllib.parse
    
    card_url = data.get('card_url')
    caption = data.get('caption', '')
    
    if not card_url:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'card_url is required'}),
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
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT chat_id FROM telegram_subscribers WHERE is_active = true')
    subscribers = cur.fetchall()
    
    sent_count = 0
    failed_count = 0
    
    for subscriber in subscribers:
        chat_id = subscriber['chat_id']
        
        api_url = f'https://api.telegram.org/bot{bot_token}/sendPhoto'
        params = {
            'chat_id': chat_id,
            'photo': card_url,
            'caption': caption
        }
        
        try:
            data_encoded = urllib.parse.urlencode(params).encode('utf-8')
            req = urllib.request.Request(api_url, data=data_encoded)
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                if result.get('ok'):
                    sent_count += 1
                    cur.execute(
                        'UPDATE telegram_subscribers SET last_sent_at = CURRENT_TIMESTAMP WHERE chat_id = %s',
                        (chat_id,)
                    )
                else:
                    failed_count += 1
        except Exception as e:
            failed_count += 1
            print(f'Failed to send to {chat_id}: {str(e)}')
    
    conn.commit()
    cur.close()
    conn.close()
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({
            'success': True,
            'sent_count': sent_count,
            'failed_count': failed_count
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
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'count': result['count']}),
        'isBase64Encoded': False
    }
