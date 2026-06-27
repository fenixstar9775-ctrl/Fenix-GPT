import os
import telebot
from flask import Flask, request
from openai import OpenAI

# 1. Fetch tokens from environment variables
# Note: Ensure you name them exactly like this in Render Environment Variables
BOT_TOKEN = os.environ.get("bot_token")
HF_TOKEN = os.environ.get("hf_token")

# 2. Initialize Telegram Bot and Flask App
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# 3. Initialize OpenAI client pointing to HuggingFace Router
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

# 4. Handle incoming Telegram messages
@bot.message_handler(func=lambda message: True)
def chat_with_bot(message):
    user_text = message.text
    
    # Send a typing indicator to the user while waiting for the API
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        # Call the Hugging Face model using OpenAI format
        chat_completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V4-Pro:novita",
            messages=[
                {
                    "role": "user",
                    "content": user_text,
                }
            ],
        )
        
        # Extract response text and reply
        bot_reply = chat_completion.choices[0].message.content
        bot.reply_to(message, bot_reply)
        
    except Exception as e:
        bot.reply_to(message, f"Sorry, I encountered an error: {str(e)}")


# 5. Flask Routes for Webhook
@app.route('/', methods=['GET'])
def index():
    return "Telegram Bot is running smoothly on Render!", 200

@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    # Receive updates from Telegram and pass them to the bot
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Forbidden', 403

# 6. Set Webhook on Startup
if __name__ == "__main__":
    # Remove any existing webhooks
    bot.remove_webhook()
    
    # Render automatically provides RENDER_EXTERNAL_URL to web services
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if render_url:
        # Set the webhook to your Render URL + bot token path
        bot.set_webhook(url=f"{render_url}/{BOT_TOKEN}")
    
    # Start the Flask app
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
