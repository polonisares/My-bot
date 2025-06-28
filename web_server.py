from flask import Flask, jsonify
import threading
import asyncio
import os
from bot import ProTankiBot

app = Flask(__name__)

# Global bot instance
bot_instance = None

@app.route('/')
def home():
    """Health check endpoint for monitoring services"""
    return jsonify({
        "status": "online",
        "service": "ProTanki Discord Bot",
        "message": "Bot is running and healthy"
    })

@app.route('/health')
def health():
    """Detailed health check"""
    bot_status = "connected" if bot_instance and not bot_instance.is_closed() else "disconnected"
    
    return jsonify({
        "status": "healthy",
        "bot_status": bot_status,
        "guilds": len(bot_instance.guilds) if bot_instance else 0,
        "uptime": "running"
    })

@app.route('/ping')
def ping():
    """Simple ping endpoint"""
    return "pong"

def run_bot():
    """Run the Discord bot in a separate thread"""
    global bot_instance
    
    # Check for required environment variables
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("Error: DISCORD_TOKEN not found")
        return
    
    # Create and run bot
    bot_instance = ProTankiBot()
    
    # Create new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(bot_instance.start(token))
    except KeyboardInterrupt:
        print("Bot shutdown requested")
    except Exception as e:
        print(f"Bot error: {e}")
    finally:
        if not bot_instance.is_closed():
            loop.run_until_complete(bot_instance.close())

def start_bot_thread():
    """Start the bot in a background thread"""
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    return bot_thread

if __name__ == '__main__':
    # Start the Discord bot in background
    print("Starting ProTanki Discord Bot...")
    start_bot_thread()
    
    # Start the Flask web server
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting web server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)