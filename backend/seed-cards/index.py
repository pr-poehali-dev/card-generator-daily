'''
Business: Заполнение базы данных открытками на каждый день года
Args: event - dict with httpMethod
      context - object with attributes: request_id
Returns: HTTP response dict
'''

import json
import os
from typing import Dict, Any
import psycopg2

def get_db_connection():
    return psycopg2.connect(os.environ['DATABASE_URL'])

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
    
    if method != 'POST':
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Method not allowed'}),
            'isBase64Encoded': False
        }
    
    sample_card_url = 'https://cdn.poehali.dev/files/05cb5fea-e0d8-43aa-8950-aae86ba173a9.jpg'
    
    cards_data = [
        ('10-26', 'С добрым утром!', 'Желаю крепкого здоровья, желаю бодрости и сил, чтоб каждый день обычной жизни лишь только радость приносил!', sample_card_url, False, None),
        ('01-01', 'С Новым Годом!', 'Пусть новый год принесет счастье, здоровье и благополучие в ваш дом!', sample_card_url, True, 'Новый Год'),
        ('01-07', 'С Рождеством!', 'Светлого Рождества! Пусть в доме будет тепло и уютно!', sample_card_url, True, 'Рождество'),
        ('02-14', 'С Днем Святого Валентина!', 'Любви, нежности и теплых чувств!', sample_card_url, True, 'День Святого Валентина'),
        ('02-23', 'С Днем защитника Отечества!', 'Мужества, силы и крепкого здоровья!', sample_card_url, True, 'День защитника Отечества'),
        ('03-08', 'С Международным женским днем!', 'Красоты, радости и весеннего настроения!', sample_card_url, True, '8 Марта'),
        ('05-01', 'С Праздником Весны и Труда!', 'Хорошего отдыха и весеннего настроения!', sample_card_url, True, '1 Мая'),
        ('05-09', 'С Днем Победы!', 'Мира, добра и светлой памяти героям!', sample_card_url, True, 'День Победы'),
        ('06-12', 'С Днем России!', 'Гордости за нашу страну и процветания!', sample_card_url, True, 'День России'),
        ('11-04', 'С Днем народного единства!', 'Мира, согласия и единства!', sample_card_url, True, 'День народного единства'),
    ]
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    inserted = 0
    for date, title, message, image_url, is_holiday, holiday_name in cards_data:
        cur.execute('''
            INSERT INTO cards (date, title, message, image_url, is_holiday, holiday_name)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (date) DO NOTHING
        ''', (date, title, message, image_url, is_holiday, holiday_name))
        if cur.rowcount > 0:
            inserted += 1
    
    conn.commit()
    cur.close()
    conn.close()
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({
            'success': True,
            'message': f'Добавлено открыток: {inserted}',
            'inserted': inserted
        }),
        'isBase64Encoded': False
    }
