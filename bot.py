import json
import os
import sys
import traceback
import discord
from openai import AsyncOpenAI

# Load configuration
if not os.path.exists("config.json"):
    print("Error: config.json not found.")
    sys.exit(1)

with open("config.json", "r") as f:
    config = json.load(f)

DISCORD_TOKEN = config.get("DISCORD_TOKEN")
GROQ_API_KEY = config.get("GROQ_API_KEY")
ALLOWED_CHANNELS = config.get("ALLOWED_CHANNEL_IDS", [])

if not DISCORD_TOKEN or DISCORD_TOKEN == "YOUR_DISCORD_BOT_TOKEN":
    print("Error: Please add your DISCORD_TOKEN in config.json")
    sys.exit(1)

if not GROQ_API_KEY or GROQ_API_KEY == "gsk_YOUR_GROQ_KEY_HERE":
    print("Error: Please add your GROQ_API_KEY in config.json")
    sys.exit(1)

# Point OpenAI client to Groq's fast API endpoint
ai_client = AsyncOpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# Set up Discord Client
intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)

SYSTEM_INSTRUCTION = "You are a helpful, fast, and friendly AI assistant in a Discord server. Keep responses concise and formatted cleanly with Discord Markdown."

@discord_client.event
async def on_ready():
    print(f"Logged in successfully as {discord_client.user.name} ({discord_client.user.id})")
    print("Groq Bot is ready and listening...")

@discord_client.event
async def on_message(message):
    if message.author == discord_client.user:
        return

    if ALLOWED_CHANNELS and message.channel.id not in ALLOWED_CHANNELS:
        return

    prompt = message.content.strip()
    if not prompt:
        return

    async with message.channel.typing():
        try:
            response = await ai_client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": SYSTEM_INSTRUCTION},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500
            )
            reply_text = response.choices[0].message.content
            if not reply_text:
                reply_text = "I received your message, but no text response was generated."

            chunks = [reply_text[i:i+1900] for i in range(0, len(reply_text), 1900)]
            for idx, chunk in enumerate(chunks):
                if idx == 0:
                    await message.reply(chunk)
                else:
                    await message.channel.send(chunk)

        except Exception as e:
            print("\n--- ERROR DETECTED ---")
            traceback.print_exc()
            print("----------------------\n")
            try:
                await message.reply("Sorry, I encountered an error generating that response.")
            except Exception:
                pass

discord_client.run(DISCORD_TOKEN)