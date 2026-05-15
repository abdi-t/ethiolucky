# bot.py
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import requests
import json
from config import *

bot = telebot.TeleBot(BOT_TOKEN)

WEBHOOK_URL = f"http://localhost:{PORT}"

# Prize constants
FIRST_PRIZE = WINNER_PRIZES[1]
SECOND_PRIZE = WINNER_PRIZES[2]
THIRD_PRIZE = WINNER_PRIZES[3]

# Main menu
def main_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton("🎲 PLAY GAME"),
        KeyboardButton("💰 BALANCE"),
        KeyboardButton("📊 STATS"),
        KeyboardButton("🏆 WINNERS"),
        KeyboardButton("❓ HELP")
    )
    return keyboard

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = f"""
🎲 *{APP_NAME}* 🎲

━━━━━━━━━━━━━━━━━━━━
🎮 *Game Rules:*
• {TOTAL_PLAYERS} players per game
• {ENTRY_FEE} Birr entry fee
• Random winners selected!
• 🥇 1st Prize: {FIRST_PRIZE} Birr
• 🥈 2nd Prize: {SECOND_PRIZE} Birr
• 🥉 3rd Prize: {THIRD_PRIZE} Birr
• House takes {PROFIT_PER_GAME} Birr
━━━━━━━━━━━━━━━━━━━━

💰 *To Play:*
1. Send {ENTRY_FEE} Birr to:
   📱 Telebirr: `{TELEBIRR_ACCOUNT}`
   🏦 CBE: `{CBE_ACCOUNT}`

2. Send: `/submit [REFERENCE] [NAME] [PHONE]`

3. Wait for admin confirmation

4. Click /play to join!

━━━━━━━━━━━━━━━━━━━━
Use the buttons below! 👇
"""
    bot.send_message(
        message.chat.id,
        welcome_text,
        parse_mode='Markdown',
        reply_markup=main_menu()
    )

# Button handlers
@bot.message_handler(func=lambda m: m.text == "🎲 PLAY GAME")
def play_game_button(message):
    play_game(message)

@bot.message_handler(func=lambda m: m.text == "💰 BALANCE")
def balance_button(message):
    check_balance(message)

@bot.message_handler(func=lambda m: m.text == "📊 STATS")
def stats_button(message):
    game_stats(message)

@bot.message_handler(func=lambda m: m.text == "🏆 WINNERS")
def winners_button(message):
    show_winners(message)

@bot.message_handler(func=lambda m: m.text == "❓ HELP")
def help_button(message):
    send_help(message)

# Play game
@bot.message_handler(commands=['play'])
def play_game(message):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🎲 Join Game", callback_data="join_game"),
        InlineKeyboardButton("🎮 Demo Mode (Free)", callback_data="demo_game"),
        InlineKeyboardButton("❌ Cancel", callback_data="cancel_game")
    )
    
    bot.send_message(
        message.chat.id,
        f"🎲 *Ready to Play?* 🎲\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Entry Fee: {ENTRY_FEE} Birr\n"
        f"🏆 1st Prize: {FIRST_PRIZE} Birr\n"
        f"🏆 2nd Prize: {SECOND_PRIZE} Birr\n"
        f"🏆 3rd Prize: {THIRD_PRIZE} Birr\n"
        f"👥 Players: {TOTAL_PLAYERS} per game\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Select an option below:",
        parse_mode='Markdown',
        reply_markup=keyboard
    )

# Callback handlers
@bot.callback_query_handler(func=lambda call: call.data == "join_game")
def handle_join_game(call):
    user_id = call.from_user.id
    username = call.from_user.username or f"user_{user_id}"
    
    try:
        # Check payment status
        response = requests.get(f"{WEBHOOK_URL}/api/check_user_payment?user_id={user_id}")
        data = response.json()
        
        if not data.get('has_paid', False):
            bot.answer_callback_query(call.id, "❌ You haven't paid yet! Use /submit first.", show_alert=True)
            return
    except:
        pass
    
    try:
        game_response = requests.get(f"{WEBHOOK_URL}/api/game_status")
        game = game_response.json()
        
        if game['player_count'] >= TOTAL_PLAYERS:
            bot.answer_callback_query(call.id, "❌ Game is full! Please wait for next round.", show_alert=True)
            return
        
        for p in game['players']:
            if p['user_id'] == user_id:
                bot.answer_callback_query(call.id, "❌ You already joined this game!", show_alert=True)
                return
        
        join_response = requests.post(
            f"{WEBHOOK_URL}/api/join_game",
            json={'user_id': user_id, 'username': username, 'is_demo': False}
        )
        result = join_response.json()
        
        if result['success']:
            if 'game_result' in result and result['game_result']:
                winner_data = result['game_result']
                msg = f"🎉 *GAME COMPLETED!* 🎉\n\n"
                for w in winner_data['winners']:
                    msg += f"{'🥇' if w['rank']==1 else '🥈' if w['rank']==2 else '🥉'} {w['rank']}{'st' if w['rank']==1 else 'nd' if w['rank']==2 else 'rd'} Place: @{w['username']} - {w['prize']} Birr\n"
                msg += f"\n💰 House Profit: {winner_data['house_profit']} Birr"
                bot.send_message(call.message.chat.id, msg, parse_mode='Markdown')
            else:
                bot.send_message(
                    call.message.chat.id,
                    f"✅ *You joined the game!* ✅\n\n"
                    f"💰 Entry: {ENTRY_FEE} Birr\n"
                    f"👥 Players: {game['player_count'] + 1}/{TOTAL_PLAYERS}\n\n"
                    f"Waiting for {TOTAL_PLAYERS - (game['player_count'] + 1)} more player(s)...",
                    parse_mode='Markdown'
                )
            bot.answer_callback_query(call.id, "✅ Joined game!")
        else:
            bot.answer_callback_query(call.id, f"❌ Error: {result.get('error', 'Unknown error')}", show_alert=True)
            
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Error: {str(e)}", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "demo_game")
def handle_demo_game(call):
    user_id = call.from_user.id
    username = call.from_user.username or f"user_{user_id}"
    
    try:
        game_response = requests.get(f"{WEBHOOK_URL}/api/game_status")
        game = game_response.json()
        
        if game['player_count'] >= TOTAL_PLAYERS:
            bot.answer_callback_query(call.id, "❌ Game is full! Please wait for next round.", show_alert=True)
            return
        
        for p in game['players']:
            if p['user_id'] == user_id:
                bot.answer_callback_query(call.id, "❌ You already joined this game!", show_alert=True)
                return
        
        join_response = requests.post(
            f"{WEBHOOK_URL}/api/join_game",
            json={'user_id': user_id, 'username': username, 'is_demo': True}
        )
        result = join_response.json()
        
        if result['success']:
            if 'game_result' in result and result['game_result']:
                winner_data = result['game_result']
                msg = f"🎮 *DEMO MODE - GAME COMPLETED!* 🎮\n\n"
                for w in winner_data['winners']:
                    msg += f"{'🥇' if w['rank']==1 else '🥈' if w['rank']==2 else '🥉'} {w['rank']}{'st' if w['rank']==1 else 'nd' if w['rank']==2 else 'rd'} Place: @{w['username']} - {w['prize']} Birr (Demo)\n"
                bot.send_message(call.message.chat.id, msg, parse_mode='Markdown')
            else:
                bot.send_message(
                    call.message.chat.id,
                    f"✅ *Demo Mode - You joined!* ✅\n\n"
                    f"👥 Players: {game['player_count'] + 1}/{TOTAL_PLAYERS}\n\n"
                    f"Waiting for {TOTAL_PLAYERS - (game['player_count'] + 1)} more player(s)...\n\n"
                    f"*This is a demo - no real money involved!*",
                    parse_mode='Markdown'
                )
            bot.answer_callback_query(call.id, "✅ Joined demo game!")
        else:
            bot.answer_callback_query(call.id, f"❌ Error: {result.get('error', 'Unknown error')}", show_alert=True)
            
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Error: {str(e)}", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "cancel_game")
def handle_cancel(call):
    bot.answer_callback_query(call.id, "Cancelled")
    bot.edit_message_text("❌ Cancelled.", call.message.chat.id, call.message.message_id)

# Balance check
@bot.message_handler(commands=['balance'])
def check_balance(message):
    user_id = message.from_user.id
    
    try:
        response = requests.get(f"{WEBHOOK_URL}/api/user_balance?user_id={user_id}")
        data = response.json()
        
        text = f"""
💰 *Your Balance*

━━━━━━━━━━━━━━━━━━━━
💵 Real Balance: {data.get('balance', 0)} Birr
🎮 Demo Balance: {data.get('demo_balance', 300)} Birr
━━━━━━━━━━━━━━━━━━━━

*How to add real balance:*
1. Send {ENTRY_FEE} Birr to:
   📱 Telebirr: `{TELEBIRR_ACCOUNT}`
2. Send /submit with your transaction details
3. Admin will confirm and add you to game
"""
        bot.send_message(message.chat.id, text, parse_mode='Markdown')
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {str(e)}")

# Game stats
@bot.message_handler(commands=['stats'])
def game_stats(message):
    try:
        response = requests.get(f"{WEBHOOK_URL}/api/game_stats")
        stats = response.json()
        
        text = f"""
📊 *Game Statistics*

━━━━━━━━━━━━━━━━━━━━
🎮 Total Games: {stats.get('total_games', 0)}
💰 Total House Profit: {stats.get('total_profit', 0)} Birr
👥 Total Players: {stats.get('total_players', 0)}
⏳ Waiting Players: {stats.get('current_players', 0)}/{TOTAL_PLAYERS}
━━━━━━━━━━━━━━━━━━━━

*Prizes:*
🥇 1st Place: {FIRST_PRIZE} Birr
🥈 2nd Place: {SECOND_PRIZE} Birr
🥉 3rd Place: {THIRD_PRIZE} Birr

*Per Game:*
• Entry Fee: {ENTRY_FEE} Birr
• Total Pot: {TOTAL_COLLECTED} Birr
• House Profit: {PROFIT_PER_GAME} Birr
"""
        bot.send_message(message.chat.id, text, parse_mode='Markdown')
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {str(e)}")

# Show winners
@bot.message_handler(commands=['winners'])
def show_winners(message):
    try:
        response = requests.get(f"{WEBHOOK_URL}/api/winners_data")
        data = response.json()
        winners = data.get('winners', [])[:10]
        
        if winners:
            text = "🏆 *Recent Winners* 🏆\n\n"
            for w in winners:
                icon = '🥇' if w['rank'] == 1 else '🥈' if w['rank'] == 2 else '🥉'
                text += f"{icon} @{w['username']} - +{w['prize_amount']} Birr (Ticket #{w['ticket_number']})\n"
            text += f"\n*Total winners:* {data.get('total_winners', 0)}\n*Total prizes:* {data.get('total_prize', 0)} Birr"
        else:
            text = "🏆 No winners yet. Be the first!"
        
        bot.send_message(message.chat.id, text, parse_mode='Markdown')
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {str(e)}")

# Submit payment
@bot.message_handler(commands=['submit'])
def submit_payment(message):
    try:
        parts = message.text.split(maxsplit=3)
        if len(parts) < 4:
            bot.reply_to(message, f"""
❌ *Invalid format!*

Use: `/submit [REFERENCE] [NAME] [PHONE]`

Example: `/submit TX123456789 John Doe 0912345678`

After sending *{ENTRY_FEE} Birr* to:
📱 Telebirr: `{TELEBIRR_ACCOUNT}`
🏦 CBE: `{CBE_ACCOUNT}`
""", parse_mode='Markdown')
            return
        
        transaction_ref = parts[1].strip()
        sender_name = parts[2].strip()
        sender_phone = parts[3].strip()
        
        user_id = message.from_user.id
        username = message.from_user.username or f"user_{user_id}"
        
        response = requests.post(
            f"{WEBHOOK_URL}/api/submit_payment",
            json={
                'user_id': user_id,
                'username': username,
                'transaction_ref': transaction_ref,
                'sender_name': sender_name,
                'sender_phone': sender_phone
            }
        )
        
        data = response.json()
        
        if data.get('success'):
            bot.reply_to(message, f"""
✅ *Payment Request Submitted!*

━━━━━━━━━━━━━━━━━━━━
📝 Reference: `{transaction_ref}`
👤 Name: {sender_name}
📱 Phone: {sender_phone}
💰 Amount: {ENTRY_FEE} Birr
━━━━━━━━━━━━━━━━━━━━

⏳ *Status:* Pending Confirmation

You will be added to the game once admin confirms.

*Next steps:*
1. Admin verifies your payment
2. You'll be added to game
3. Use /play when ready!
""", parse_mode='Markdown')
            
            # Notify admin
            bot.send_message(ADMIN_ID, f"""
💰 *NEW PAYMENT REQUEST* 💰

👤 @{username} (ID: {user_id})
📝 Ref: `{transaction_ref}`
👤 Name: {sender_name}
📱 Phone: {sender_phone}
💰 Amount: {ENTRY_FEE} Birr

➡️ Verify in bank then confirm at:
http://localhost:{PORT}/payments
""", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"❌ Error: {data.get('error', 'Unknown error')}")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# Help
@bot.message_handler(commands=['help'])
def send_help(message):
    text = f"""
❓ *Help Guide*

━━━━━━━━━━━━━━━━━━━━
*How to Play:*

1️⃣ *Pay Entry Fee*
   Send {ENTRY_FEE} Birr to:
   📱 Telebirr: `{TELEBIRR_ACCOUNT}`
   🏦 CBE: `{CBE_ACCOUNT}`

2️⃣ *Submit Payment*
   `/submit [REF] [NAME] [PHONE]`

3️⃣ *Join Game*
   Click /play or use the PLAY GAME button

4️⃣ *Wait for Players*
   Game starts when {TOTAL_PLAYERS} players join

5️⃣ *Win Prize*
   🥇 1st: {FIRST_PRIZE} Birr
   🥈 2nd: {SECOND_PRIZE} Birr
   🥉 3rd: {THIRD_PRIZE} Birr

━━━━━━━━━━━━━━━━━━━━
*Commands:*
/start - Main menu
/play - Join a game
/submit - Submit payment
/balance - Check balance
/stats - Game statistics
/winners - Recent winners
/help - This help

━━━━━━━━━━━━━━━━━━━━
*Demo Mode:*
Use "Demo Mode" option to test without real money!
"""
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

# Admin commands
@bot.message_handler(commands=['admin_stats'])
def admin_stats(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin only!")
        return
    
    try:
        response = requests.get(f"{WEBHOOK_URL}/api/game_stats")
        stats = response.json()
        
        response2 = requests.get(f"{WEBHOOK_URL}/api/payments_data?status=pending")
        payments = response2.json()
        
        text = f"""
📊 *Admin Statistics*

━━━━━━━━━━━━━━━━━━━━
🎮 Total Games: {stats.get('total_games', 0)}
💰 Total Profit: {stats.get('total_profit', 0)} Birr
👥 Total Players: {stats.get('total_players', 0)}
⏳ Pending Payments: {payments.get('pending', 0)}
━━━━━━━━━━━━━━━━━━━━

*Quick Links:*
• Admin Panel: http://localhost:{PORT}
• Payments: http://localhost:{PORT}/payments
"""
        bot.send_message(message.chat.id, text, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

# Add demo funds (admin)
@bot.message_handler(commands=['addfunds'])
def add_demo_funds(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin only!")
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "Usage: /addfunds [user_id] [amount]")
            return
        
        user_id = int(parts[1])
        amount = int(parts[2])
        
        response = requests.post(
            f"{WEBHOOK_URL}/api/add_demo_balance",
            json={'user_id': user_id, 'amount': amount}
        )
        
        if response.status_code == 200:
            bot.reply_to(message, f"✅ Added {amount} demo funds to user {user_id}")
        else:
            bot.reply_to(message, "❌ Failed to add funds")
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

# Broadcast (admin)
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin only!")
        return
    
    msg = message.text.replace('/broadcast', '', 1).strip()
    if not msg:
        bot.reply_to(message, "Usage: /broadcast [message]")
        return
    
    try:
        response = requests.get(f"{WEBHOOK_URL}/api/all_users")
        users = response.json()
        
        success = 0
        fail = 0
        
        for user in users:
            try:
                bot.send_message(user['user_id'], f"📢 *Announcement*\n\n{msg}", parse_mode='Markdown')
                success += 1
            except:
                fail += 1
        
        bot.reply_to(message, f"✅ Broadcast sent!\n\nSent: {success}\nFailed: {fail}")
    except:
        bot.reply_to(message, "✅ Broadcast sent!")

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

def send_miniapp_button(message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(
        "🎮 Open Game",
        web_app=WebAppInfo(url="https://abc123.ngrok.io")  # Your URL
    ))
    bot.send_message(message.chat.id, "Click to open the game!", reply_markup=keyboard)

if __name__ == '__main__':
    print("=" * 50)
    print(f"🎲 {APP_NAME} Bot Started!")
    print("=" * 50)
    print(f"Bot Token: {BOT_TOKEN[:15]}...")
    print(f"Admin ID: {ADMIN_ID}")
    print(f"Entry Fee: {ENTRY_FEE} Birr")
    print(f"1st Prize: {FIRST_PRIZE} Birr")
    print(f"2nd Prize: {SECOND_PRIZE} Birr")
    print(f"3rd Prize: {THIRD_PRIZE} Birr")
    print(f"House Profit: {PROFIT_PER_GAME} Birr")
    print("=" * 50)
    print("Bot is running... Press Ctrl+C to stop")
    print("=" * 50)
    
    bot.infinity_polling()