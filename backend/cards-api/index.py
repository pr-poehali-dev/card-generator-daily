'''
Business: API для управления открытками (получение открытки дня, список открыток)
Args: event - dict with httpMethod, queryStringParameters
      context - object with attributes: request_id, function_name
Returns: HTTP response dict
'''

import json
import os
from typing import Dict, Any
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method: str = event.get('httpMethod', 'GET')
    
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
    
    if method == 'GET':
        params = event.get('queryStringParameters') or {}
        action = params.get('action', 'today')
        
        if action == 'today':
            return get_today_card()
        elif action == 'all':
            return get_all_cards()
        elif action == 'date':
            date = params.get('date')
            return get_card_by_date(date)
        
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Unknown action'}),
            'isBase64Encoded': False
        }
    
    if method == 'POST':
        body_data = json.loads(event.get('body', '{}'))
        return create_card(body_data)
    
    return {
        'statusCode': 405,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'error': 'Method not allowed'}),
        'isBase64Encoded': False
    }

def get_today_card() -> Dict[str, Any]:
    today = datetime.now()
    date_str = f'{today.month:02d}-{today.day:02d}'
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM cards WHERE date = %s', (date_str,))
    card = cur.fetchone()
    cur.close()
    conn.close()
    
    if not card:
        return {
            'statusCode': 404,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Открытка на сегодня не найдена'}),
            'isBase64Encoded': False
        }
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps(dict(card), default=str),
        'isBase64Encoded': False
    }

def get_card_by_date(date: str) -> Dict[str, Any]:
    if not date:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'date parameter required (MM-DD format)'}),
            'isBase64Encoded': False
        }
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM cards WHERE date = %s', (date,))
    card = cur.fetchone()
    cur.close()
    conn.close()
    
    if not card:
        return {
            'statusCode': 404,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Открытка не найдена'}),
            'isBase64Encoded': False
        }
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps(dict(card), default=str),
        'isBase64Encoded': False
    }

def get_all_cards() -> Dict[str, Any]:
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM cards ORDER BY date ASC')
    cards = cur.fetchall()
    cur.close()
    conn.close()
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps([dict(card) for card in cards], default=str),
        'isBase64Encoded': False
    }

def create_card(data: Dict[str, Any]) -> Dict[str, Any]:
    date = data.get('date')
    title = data.get('title')
    message = data.get('message')
    image_url = data.get('image_url')
    is_holiday = data.get('is_holiday', False)
    holiday_name = data.get('holiday_name')
    
    if not all([date, title, message, image_url]):
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'date, title, message, image_url are required'}),
            'isBase64Encoded': False
        }
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute('''
        INSERT INTO cards (date, title, message, image_url, is_holiday, holiday_name)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (date) 
        DO UPDATE SET 
            title = EXCLUDED.title,
            message = EXCLUDED.message,
            image_url = EXCLUDED.image_url,
            is_holiday = EXCLUDED.is_holiday,
            holiday_name = EXCLUDED.holiday_name
        RETURNING id
    ''', (date, title, message, image_url, is_holiday, holiday_name))
    
    result = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'success': True, 'card_id': result['id']}),
        'isBase64Encoded': False
    }
