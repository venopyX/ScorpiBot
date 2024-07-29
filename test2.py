import requests
from config import API_BASE_URL, API_TOKEN
from instruction import Instruction
import logging

logger = logging.getLogger(__name__)

class ScorpiAPI:
    @staticmethod
    def get_response(user_message="What is the weather like today?"):
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        inputs = [
            {"role": "system", "content": Instruction.system_prompt()},
            {"role": "user", "content": user_message}
        ]

        try:
            response = requests.post(f"{API_BASE_URL}@cf/meta/llama-3-8b-instruct", headers=headers, json={"messages": inputs})
            response.raise_for_status()
            response_data = response.json()
            logger.debug(f"API response data: {response_data}")
            
            # Extract the response text
            if response_data.get('success', False):
                return response_data['result']['response']
            else:
                logger.error(f"API response error: {response_data.get('errors')}")
                return "Oops! Something went wrong. 😅"
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return "Oops! Something went wrong. 😅"

# Example usage
if __name__ == "__main__":
    api = ScorpiAPI()
    response = api.get_response()  # This will use the default example message
    print(response)
