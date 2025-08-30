import json

def handler(request):
    """Debug endpoint to see what Vercel passes as request object"""
    
    try:
        # Let's see what the request object actually contains
        request_info = {
            'type': str(type(request)),
            'attributes': dir(request),
            'method': getattr(request, 'method', 'NO_METHOD_ATTR'),
            'headers': getattr(request, 'headers', 'NO_HEADERS_ATTR'),
            'body': getattr(request, 'body', 'NO_BODY_ATTR'),
            'query': getattr(request, 'query', 'NO_QUERY_ATTR'),
            'url': getattr(request, 'url', 'NO_URL_ATTR'),
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(request_info, default=str, indent=2)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e),
                'error_type': type(e).__name__
            })
        }