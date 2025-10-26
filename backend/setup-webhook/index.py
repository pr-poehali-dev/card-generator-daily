'''
Business: Настройка webhook для Telegram бота
Args: event - dict with httpMethod, queryStringParameters
      context - object with attributes: request_id
Returns: HTTP response dict
'''

import json
import os
from typing import Dict, Any
import urllib.request
import urllib.parse

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method: str = event.get('httpMethod', 'POST')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
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
    
    bot_function_url = os.environ.get('TELEGRAM_BOT_WEBHOOK_URL')
    if not bot_function_url:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'TELEGRAM_BOT_WEBHOOK_URL not configured'}),
            'isBase64Encoded': False
        }
    
    if method == 'POST':
        api_url = f'https://api.telegram.org/bot{bot_token}/setWebhook'
        params = {
            'url': bot_function_url,
            'drop_pending_updates': 'true'
        }
        
        try:
            data_encoded = urllib.parse.urlencode(params).encode('utf-8')
            req = urllib.request.Request(api_url, data=data_encoded)
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                if result.get('ok'):
                    return {
                        'statusCode': 200,
                        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                        'body': json.dumps({
                            'success': True,
                            'message': 'Webhook успешно настроен!',
                            'webhook_url': bot_function_url
                        }),
                        'isBase64Encoded': False
                    }
                else:
                    return {
                        'statusCode': 400,
                        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                        'body': json.dumps({
                            'error': 'Failed to set webhook',
                            'details': result.get('description', 'Unknown error')
                        }),
                        'isBase64Encoded': False
                    }
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': f'Exception: {str(e)}'}),
                'isBase64Encoded': False
            }
    
    if method == 'GET':
        api_url = f'https://api.telegram.org/bot{bot_token}/getWebhookInfo'
        
        try:
            req = urllib.request.Request(api_url)
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                if result.get('ok'):
                    webhook_info = result.get('result', {})
                    return {
                        'statusCode': 200,
                        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                        'body': json.dumps({
                            'webhook_url': webhook_info.get('url', ''),
                            'has_custom_certificate': webhook_info.get('has_custom_certificate', False),
                            'pending_update_count': webhook_info.get('pending_update_count', 0),
                            'last_error_date': webhook_info.get('last_error_date'),
                            'last_error_message': webhook_info.get('last_error_message'),
                            'max_connections': webhook_info.get('max_connections', 40)
                        }),
                        'isBase64Encoded': False
                    }
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': f'Exception: {str(e)}'}),
                'isBase64Encoded': False
            }
    
    return {
        'statusCode': 405,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'error': 'Method not allowed'}),
        'isBase64Encoded': False
    }
