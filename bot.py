import requests
import os
from flask import Flask, request

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Use environment variable
URL = f"https://api.telegram.org/bot{TOKEN}/"
app = Flask(__name__)

def send_message(chat_id, text):
    params = {"chat_id": chat_id, "text": text}
    requests.get(URL + "sendMessage", params=params)

def send_photo_description(chat_id, photo_url):
    api_url = f"https://api.zetsu.xyz/gemini?prompt=describe%20this%20photo&url={photo_url}"
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        send_message(chat_id, data.get("gemini", "No description available."))
    else:
        send_message(chat_id, "Error: Failed to analyze the image.")

def process_message(update):
    message = update.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")
    photos = message.get("photo", [])

    if text.startswith("/question"):
        query = text.replace("/question", "").strip()
        if query:
            api_url = f"https://api.zetsu.xyz/ai/hermes-2-pro?q={query}&uid=110031841"
            response = requests.get(api_url)
            if response.status_code == 200:
                data = response.json()
                if data.get("status"):
                    send_message(chat_id, data.get("result"))
                else:
                    send_message(chat_id, "Error: Invalid response from API")
            else:
                send_message(chat_id, "Error: Failed to reach API")
        else:
            send_message(chat_id, "Usage: /question <your question>")
    elif photos:
        file_id = photos[-1]["file_id"]
        file_info = requests.get(URL + f"getFile?file_id={file_id}").json()
        if "result" in file_info:
            file_path = file_info["result"]["file_path"]
            photo_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
            send_photo_description(chat_id, photo_url)

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()
    process_message(update)
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
