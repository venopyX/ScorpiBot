# utils.py
import requests
from config import API_BASE_URL, API_TOKEN
from instruction import Instruction

class ScorpiAPI:
    @staticmethod
    def get_response(user_message):
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        inputs = [
            {"role": "system", "content": Instruction.system_prompt()},
            {"role": "user", "content": user_message}
        ]

        response = requests.post(f"{API_BASE_URL}@cf/meta/llama-3-8b-instruct", headers=headers, json={"messages": inputs})
        return response.json().get('choices', [{}])[0].get('message', {}).get('content', 'Oops! Something went wrong. 😅')
