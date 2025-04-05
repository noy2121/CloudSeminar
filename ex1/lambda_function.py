import os
import json
import time
import boto3
from boto3.dynamodb.conditions import Key
from typing import Dict, Any, Optional, List

import openai


client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
dynamodb = boto3.resource("dynamodb")

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type"
}
MODEL_NAME = "gpt-3.5-turbo"
TABLE_NAME = os.environ.get("TABLE_NAME", "chat-history")


def get_current_timestamp() -> int:
    return int(time.time() * 1000)


def get_last_messages(table, user_id: str) -> List[Dict[str, Any]]:
    if not user_id:
        return []

    response = table.query(
        KeyConditionExpression=Key("user_id").eq(user_id),
        ScanIndexForward=False,
        Limit=6
    )
    return sorted(response.get("Items", []), key=lambda x: x.get("timestamp", 0))


def save_message(table, user_id: str, role: str, content: str):
    if not user_id:
        return

    table.put_item(
        Item={
            "user_id": user_id,
            "timestamp": get_current_timestamp(),
            "role": role,
            "content": content
        }
    )


def build_response(status_code: int, body: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    response = {
        "statusCode": status_code,
        "headers": headers or CORS_HEADERS,
        "body": json.dumps(body)
    }
    return response


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    
    # initialize dynamodb table
    table = dynamodb.Table(TABLE_NAME)

    # extract HTTP method
    user_method = event.get("requestContext", {}).get("http", {}).get("method")
    
    # handle CORS preflight request
    if user_method == "OPTIONS":
        return build_response(200, {"message": "CORS preflight request successful"})
    
    if user_method != "POST":
        return build_response(405, {"error": "Only POST method is allowed"})
    
    try:
        body = json.loads(event.get("body", "{}"))
        user_id = body.get("user_id")
        user_prompt = body.get("user_prompt")
        if not user_prompt:
            return build_response(400, {"error": "Missing 'user_prompt' in request body"})
        
        history = get_last_messages(table, user_id)
        messages = [{"role": item["role"], "content": item["content"]} for item in history]
        messages.append({"role": "user", "content": user_prompt})


        # call OpenAI API
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages
        )
        
        ai_reply = response.choices[0].message.content

        save_message(table, user_id, "user", user_prompt)
        save_message(table, user_id, "assistant", ai_reply)

        return build_response(200, {"ai_reply": ai_reply})
        
    except json.JSONDecodeError:
        return build_response(400, {"error": "Invalid JSON in request body"})
    except Exception as e:
        return build_response(500, {"error": str(e)})