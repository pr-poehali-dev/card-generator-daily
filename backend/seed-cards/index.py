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
    
    cards_data = [
        ('10-26', 'С добрым утром!', 'Желаю крепкого здоровья, желаю бодрости и сил, чтоб каждый день обычной жизни лишь только радость приносил!', 'https://i.pinimg.com/originals/bf/65/71/bf6571d0fc24c2a8feb4d0b4a1a6ce07.jpg', False, None),
        ('01-01', 'С Новым Годом!', 'Пусть новый год принесет счастье, здоровье и благополучие в ваш дом!', 'https://i.pinimg.com/originals/29/86/e3/2986e3c70f2cdf2b3a7b88e583e4a03e.jpg', True, 'Новый Год'),
        ('01-07', 'С Рождеством!', 'Светлого Рождества! Пусть в доме будет тепло и уютно!', 'https://i.pinimg.com/originals/53/a8/f1/53a8f160d7d4ddf74c6e5cd9c0a8dd2e.jpg', True, 'Рождество'),
        ('02-14', 'С Днем Святого Валентина!', 'Любви, нежности и теплых чувств!', 'https://i.pinimg.com/originals/e0/8e/1d/e08e1d0c5c8f3c38a2c5c3a1e1f4a6b3.jpg', True, 'День Святого Валентина'),
        ('02-23', 'С Днем защитника Отечества!', 'Мужества, силы и крепкого здоровья!', 'https://i.pinimg.com/originals/92/73/46/9273461f1e8e8c0e6a7c3b2e1f4a6b3c.jpg', True, 'День защитника Отечества'),
        ('03-08', 'С Международным женским днем!', 'Красоты, радости и весеннего настроения!', 'https://i.pinimg.com/originals/7d/45/97/7d45975b8f0f3c38a2c5c3a1e1f4a6b3.jpg', True, '8 Марта'),
        ('05-01', 'С Праздником Весны и Труда!', 'Хорошего отдыха и весеннего настроения!', 'https://i.pinimg.com/originals/1a/2b/3c/1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p.jpg', True, '1 Мая'),
        ('05-09', 'С Днем Победы!', 'Мира, добра и светлой памяти героям!', 'https://i.pinimg.com/originals/a5/b6/c7/a5b6c7d8e9f0g1h2i3j4k5l6m7n8o9p0.jpg', True, 'День Победы'),
        ('06-12', 'С Днем России!', 'Гордости за нашу страну и процветания!', 'https://i.pinimg.com/originals/45/67/89/456789abcdef0123456789abcdef0123.jpg', True, 'День России'),
        ('11-04', 'С Днем народного единства!', 'Мира, согласия и единства!', 'https://i.pinimg.com/originals/67/89/ab/6789abcdef0123456789abcdef012345.jpg', True, 'День народного единства'),
        ('01-15', 'С добрым утром!', 'Пусть этот день принесет вам радость и удачу!', 'https://i.pinimg.com/originals/bf/65/71/bf6571d0fc24c2a8feb4d0b4a1a6ce07.jpg', False, None),
        ('02-10', 'Доброго дня!', 'Желаю тепла, уюта и хорошего настроения!', 'https://i.pinimg.com/originals/c1/d2/e3/c1d2e3f4g5h6i7j8k9l0m1n2o3p4q5r6.jpg', False, None),
        ('03-15', 'С добрым утром!', 'Пусть весна принесет тепло и новые возможности!', 'https://i.pinimg.com/originals/s7/t8/u9/s7t8u9v0w1x2y3z4a5b6c7d8e9f0g1h2.jpg', False, None),
        ('04-20', 'Чудесного дня!', 'Пусть каждый момент будет наполнен радостью!', 'https://i.pinimg.com/originals/i3/j4/k5/i3j4k5l6m7n8o9p0q1r2s3t4u5v6w7x8.jpg', False, None),
        ('05-20', 'Доброго утра!', 'Пусть этот день будет ярким и счастливым!', 'https://i.pinimg.com/originals/y9/z0/a1/y9z0a1b2c3d4e5f6g7h8i9j0k1l2m3n4.jpg', False, None),
        ('06-25', 'С добрым утром!', 'Желаю солнечного настроения и приятных моментов!', 'https://i.pinimg.com/originals/o5/p6/q7/o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0.jpg', False, None),
        ('07-15', 'Прекрасного дня!', 'Пусть лето дарит яркие впечатления!', 'https://i.pinimg.com/originals/e1/f2/g3/e1f2g3h4i5j6k7l8m9n0o1p2q3r4s5t6.jpg', False, None),
        ('08-10', 'Доброго утра!', 'Желаю легкости и вдохновения на весь день!', 'https://i.pinimg.com/originals/u7/v8/w9/u7v8w9x0y1z2a3b4c5d6e7f8g9h0i1j2.jpg', False, None),
        ('09-15', 'С добрым утром!', 'Пусть осень принесет тепло и уют!', 'https://i.pinimg.com/originals/k3/l4/m5/k3l4m5n6o7p8q9r0s1t2u3v4w5x6y7z8.jpg', False, None),
        ('10-10', 'Чудесного дня!', 'Желаю ярких красок и приятных встреч!', 'https://i.pinimg.com/originals/a9/b0/c1/a9b0c1d2e3f4g5h6i7j8k9l0m1n2o3p4.jpg', False, None),
        ('11-15', 'С добрым утром!', 'Пусть день будет наполнен теплом и заботой!', 'https://i.pinimg.com/originals/q5/r6/s7/q5r6s7t8u9v0w1x2y3z4a5b6c7d8e9f0.jpg', False, None),
        ('12-20', 'Прекрасного дня!', 'Желаю волшебного настроения и радости!', 'https://i.pinimg.com/originals/g1/h2/i3/g1h2i3j4k5l6m7n8o9p0q1r2s3t4u5v6.jpg', False, None),
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