# database.py
import sqlite3
import random
from datetime import datetime
from contextlib import contextmanager
from config import DATABASE_PATH, ENTRY_FEE, TOTAL_PLAYERS, WINNER_PRIZES, PROFIT_PER_GAME, DEMO_BALANCE_START

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_database():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                username TEXT,
                phone TEXT,
                balance INTEGER DEFAULT 0,
                demo_balance INTEGER DEFAULT {DEMO_BALANCE_START},
                is_demo INTEGER DEFAULT 0,
                total_spent INTEGER DEFAULT 0,
                total_won INTEGER DEFAULT 0,
                games_played INTEGER DEFAULT 0,
                games_won INTEGER DEFAULT 0,
                joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Game sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER UNIQUE,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                status TEXT DEFAULT 'waiting',
                total_players INTEGER DEFAULT 0,
                winner1_id INTEGER,
                winner2_id INTEGER,
                winner3_id INTEGER,
                winner1_prize INTEGER,
                winner2_prize INTEGER,
                winner3_prize INTEGER,
                total_collected INTEGER DEFAULT 0,
                total_paid INTEGER DEFAULT 0,
                house_profit INTEGER DEFAULT 0
            )
        ''')
        
        # Entries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                user_id INTEGER,
                username TEXT,
                ticket_number INTEGER,
                entry_time TIMESTAMP,
                payment_status TEXT DEFAULT 'pending'
            )
        ''')
        
        # Winners table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS winners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                user_id INTEGER,
                username TEXT,
                rank INTEGER,
                prize_amount INTEGER,
                ticket_number INTEGER,
                paid_time TIMESTAMP
            )
        ''')
        
        # Payment requests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                amount INTEGER,
                transaction_ref TEXT UNIQUE,
                sender_name TEXT,
                sender_phone TEXT,
                status TEXT DEFAULT 'pending',
                requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                confirmed_at TIMESTAMP,
                confirmed_by TEXT,
                notes TEXT
            )
        ''')
        
        # Admin users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            )
        ''')
        
        # Insert default admin
        cursor.execute("INSERT OR IGNORE INTO admin_users (username, password) VALUES ('admin', 'admin123')")
        
        # Create default game session if none exists
        cursor.execute("SELECT COUNT(*) as count FROM game_sessions")
        result = cursor.fetchone()
        if result['count'] == 0:
            new_session_id = random.randint(100, 999)
            cursor.execute('''
                INSERT INTO game_sessions (session_id, start_time, status)
                VALUES (?, ?, 'waiting')
            ''', (new_session_id, datetime.now()))
        
        conn.commit()
        print("✅ Database initialized!")

# ========== PAYMENT FUNCTIONS ==========

def add_payment_request(user_id, username, amount, transaction_ref, sender_name, sender_phone):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM payment_requests WHERE transaction_ref = ?", (transaction_ref,))
        if cursor.fetchone():
            return False, "Duplicate transaction reference"
        
        cursor.execute('''
            INSERT INTO payment_requests (user_id, username, amount, transaction_ref, sender_name, sender_phone, status)
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
        ''', (user_id, username, amount, transaction_ref, sender_name, sender_phone))
        
        return True, cursor.lastrowid

def get_all_payments(status=None):
    with get_db() as conn:
        cursor = conn.cursor()
        
        if status and status != 'all':
            cursor.execute("SELECT * FROM payment_requests WHERE status = ? ORDER BY requested_at DESC", (status,))
        else:
            cursor.execute("SELECT * FROM payment_requests ORDER BY requested_at DESC")
        
        payments = cursor.fetchall()
        
        cursor.execute("SELECT COUNT(*) as count FROM payment_requests WHERE status = 'pending'")
        result = cursor.fetchone()
        pending = result['count'] if result else 0
        
        cursor.execute("SELECT COUNT(*) as count FROM payment_requests WHERE status = 'confirmed'")
        result = cursor.fetchone()
        confirmed = result['count'] if result else 0
        
        cursor.execute("SELECT COUNT(*) as count FROM payment_requests WHERE status = 'rejected'")
        result = cursor.fetchone()
        rejected = result['count'] if result else 0
        
        cursor.execute("SELECT SUM(amount) as total FROM payment_requests WHERE status = 'confirmed'")
        result = cursor.fetchone()
        total_amount = result['total'] if result and result['total'] else 0
        
        return {
            'payments': [dict(p) for p in payments],
            'pending': pending,
            'confirmed': confirmed,
            'rejected': rejected,
            'total_amount': total_amount
        }

def confirm_payment(payment_id, admin_username, admin_note=None):
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM payment_requests WHERE id = ?", (payment_id,))
        payment = cursor.fetchone()
        
        if not payment:
            return False, "Payment not found"
        
        if payment['status'] != 'pending':
            return False, f"Payment already {payment['status']}"
        
        cursor.execute('''
            UPDATE payment_requests 
            SET status = 'confirmed', confirmed_at = ?, confirmed_by = ?, notes = ?
            WHERE id = ?
        ''', (datetime.now(), admin_username, admin_note or 'Confirmed by admin', payment_id))
        
        # Get current active game
        cursor.execute("SELECT session_id FROM game_sessions WHERE status = 'waiting' ORDER BY start_time DESC LIMIT 1")
        game = cursor.fetchone()
        
        if not game:
            new_session_id = random.randint(100, 999)
            cursor.execute('''
                INSERT INTO game_sessions (session_id, start_time, status)
                VALUES (?, ?, 'waiting')
            ''', (new_session_id, datetime.now()))
            game = {'session_id': new_session_id}
        
        # Check if user already in game
        cursor.execute("SELECT id FROM entries WHERE session_id = ? AND user_id = ?", (game['session_id'], payment['user_id']))
        if not cursor.fetchone():
            ticket_number = random.randint(1000, 9999)
            cursor.execute('''
                INSERT INTO entries (session_id, user_id, username, ticket_number, entry_time, payment_status)
                VALUES (?, ?, ?, ?, ?, 'confirmed')
            ''', (game['session_id'], payment['user_id'], payment['username'], ticket_number, datetime.now()))
            
            cursor.execute('''
                UPDATE users 
                SET total_spent = total_spent + ?, games_played = games_played + 1 
                WHERE user_id = ?
            ''', (payment['amount'], payment['user_id']))
            
            if cursor.rowcount == 0:
                cursor.execute('''
                    INSERT INTO users (user_id, username, total_spent, games_played)
                    VALUES (?, ?, ?, 1)
                ''', (payment['user_id'], payment['username'], payment['amount']))
            
            cursor.execute('''
                UPDATE game_sessions 
                SET total_collected = total_collected + ?, total_players = total_players + 1
                WHERE session_id = ?
            ''', (payment['amount'], game['session_id']))
            
            # Check if game is full (20 players) and auto-play
            cursor.execute("SELECT COUNT(*) as count FROM entries WHERE session_id = ?", (game['session_id'],))
            result = cursor.fetchone()
            if result['count'] >= TOTAL_PLAYERS:
                play_game(game['session_id'])
        
        return True, "Payment confirmed and user added to game"

def reject_payment(payment_id, admin_username, reason):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE payment_requests 
            SET status = 'rejected', confirmed_at = ?, confirmed_by = ?, notes = ?
            WHERE id = ?
        ''', (datetime.now(), admin_username, reason, payment_id))
        return True

# ========== GAME FUNCTIONS ==========

def play_game(session_id):
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT user_id, username, ticket_number FROM entries WHERE session_id = ?", (session_id,))
        players = cursor.fetchall()
        
        if len(players) != TOTAL_PLAYERS:
            return False, f"Need {TOTAL_PLAYERS} players, have {len(players)}"
        
        # Randomly select winners
        players_list = list(players)
        random.shuffle(players_list)
        
        winners = []
        for rank in range(1, 4):
            winner = players_list[rank-1]
            prize = WINNER_PRIZES[rank]
            
            cursor.execute('''
                UPDATE users 
                SET balance = balance + ?, total_won = total_won + ?, games_won = games_won + 1
                WHERE user_id = ?
            ''', (prize, prize, winner['user_id']))
            
            cursor.execute('''
                INSERT INTO winners (session_id, user_id, username, rank, prize_amount, ticket_number, paid_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, winner['user_id'], winner['username'], rank, prize, winner['ticket_number'], datetime.now()))
            
            winners.append({'rank': rank, 'username': winner['username'], 'prize': prize, 'ticket': winner['ticket_number']})
        
        total_collected = TOTAL_PLAYERS * ENTRY_FEE
        total_paid = sum(WINNER_PRIZES.values())
        house_profit = total_collected - total_paid
        
        cursor.execute('''
            UPDATE game_sessions 
            SET end_time = ?, status = 'completed',
                winner1_id = ?, winner2_id = ?, winner3_id = ?,
                winner1_prize = ?, winner2_prize = ?, winner3_prize = ?,
                total_collected = ?, total_paid = ?, house_profit = ?
            WHERE session_id = ?
        ''', (datetime.now(), winners[0]['user_id'], winners[1]['user_id'], winners[2]['user_id'],
              winners[0]['prize'], winners[1]['prize'], winners[2]['prize'],
              total_collected, total_paid, house_profit, session_id))
        
        # Create new game session
        new_session_id = random.randint(100, 999)
        cursor.execute('''
            INSERT INTO game_sessions (session_id, start_time, status)
            VALUES (?, ?, 'waiting')
        ''', (new_session_id, datetime.now()))
        
        return True, {'winners': winners, 'total_collected': total_collected, 'total_paid': total_paid, 'house_profit': house_profit}

def get_game_status():
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM game_sessions WHERE status = 'waiting' ORDER BY start_time DESC LIMIT 1")
        game = cursor.fetchone()
        
        if not game:
            session_id = random.randint(100, 999)
            cursor.execute('''
                INSERT INTO game_sessions (session_id, start_time, status)
                VALUES (?, ?, 'waiting')
            ''', (session_id, datetime.now()))
            game = {'session_id': session_id, 'status': 'waiting'}
        
        cursor.execute("SELECT COUNT(*) as count FROM entries WHERE session_id = ?", (game['session_id'],))
        result = cursor.fetchone()
        player_count = result['count'] if result else 0
        
        cursor.execute("SELECT user_id, username, ticket_number FROM entries WHERE session_id = ?", (game['session_id'],))
        players = cursor.fetchall()
        
        return {
            'session_id': game['session_id'],
            'player_count': player_count,
            'target': TOTAL_PLAYERS,
            'players': [{'user_id': p['user_id'], 'username': p['username'], 'ticket_number': p['ticket_number']} for p in players],
            'can_play': player_count == TOTAL_PLAYERS
        }

# ========== STATS FUNCTIONS ==========

def get_game_stats():
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM game_sessions WHERE status = 'completed'")
        result = cursor.fetchone()
        total_games = result['count'] if result else 0
        
        cursor.execute("SELECT SUM(house_profit) as total FROM game_sessions WHERE status = 'completed'")
        result = cursor.fetchone()
        total_profit = result['total'] if result and result['total'] else 0
        
        cursor.execute("SELECT COUNT(*) as count FROM users")
        result = cursor.fetchone()
        total_players = result['count'] if result else 0
        
        cursor.execute("SELECT COUNT(*) as count FROM entries WHERE session_id = (SELECT session_id FROM game_sessions WHERE status = 'waiting' ORDER BY start_time DESC LIMIT 1)")
        result = cursor.fetchone()
        current_players = result['count'] if result else 0
        
        cursor.execute("SELECT COUNT(*) as count FROM payment_requests WHERE status = 'pending'")
        result = cursor.fetchone()
        pending = result['count'] if result else 0
        
        return {
            'total_games': total_games,
            'total_profit': total_profit,
            'total_players': total_players,
            'current_players': current_players,
            'target_players': TOTAL_PLAYERS,
            'entry_fee': ENTRY_FEE,
            'winner_prizes': WINNER_PRIZES,
            'profit_per_game': PROFIT_PER_GAME,
            'pending_payments': pending
        }

def get_all_players():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY total_won DESC")
        players = cursor.fetchall()
        
        cursor.execute("SELECT SUM(total_won) as total FROM users")
        result = cursor.fetchone()
        total_won = result['total'] if result and result['total'] else 0
        
        cursor.execute("SELECT SUM(total_spent) as total FROM users")
        result = cursor.fetchone()
        total_spent = result['total'] if result and result['total'] else 0
        
        return {
            'players': [dict(p) for p in players],
            'total_players': len(players),
            'total_won': total_won,
            'total_spent': total_spent
        }

def get_all_games():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM game_sessions WHERE status = 'completed' ORDER BY start_time DESC")
        games = cursor.fetchall()
        
        cursor.execute("SELECT SUM(total_collected) as total FROM game_sessions WHERE status = 'completed'")
        result = cursor.fetchone()
        total_collected = result['total'] if result and result['total'] else 0
        
        cursor.execute("SELECT SUM(total_paid) as total FROM game_sessions WHERE status = 'completed'")
        result = cursor.fetchone()
        total_paid = result['total'] if result and result['total'] else 0
        
        cursor.execute("SELECT SUM(house_profit) as total FROM game_sessions WHERE status = 'completed'")
        result = cursor.fetchone()
        total_profit = result['total'] if result and result['total'] else 0
        
        return {
            'games': [dict(g) for g in games],
            'total_games': len(games),
            'total_collected': total_collected,
            'total_paid': total_paid,
            'total_profit': total_profit
        }

def get_game_details(session_id):
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM game_sessions WHERE session_id = ?", (session_id,))
        game = cursor.fetchone()
        
        if not game:
            return None
        
        cursor.execute("SELECT username, ticket_number FROM entries WHERE session_id = ?", (session_id,))
        players = cursor.fetchall()
        
        cursor.execute("SELECT * FROM winners WHERE session_id = ? ORDER BY rank", (session_id,))
        winners = cursor.fetchall()
        
        return {
            'session_id': game['session_id'],
            'start_time': game['start_time'],
            'end_time': game['end_time'],
            'players': [{'username': p['username'], 'ticket': p['ticket_number']} for p in players],
            'winners': [{'rank': w['rank'], 'username': w['username'], 'prize': w['prize_amount'], 'ticket': w['ticket_number']} for w in winners],
            'total_collected': game['total_collected'],
            'total_paid': game['total_paid'],
            'house_profit': game['house_profit']
        }

def get_all_winners():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM winners ORDER BY id DESC LIMIT 50")
        winners = cursor.fetchall()
        
        cursor.execute("SELECT SUM(prize_amount) as total FROM winners")
        result = cursor.fetchone()
        total_prize = result['total'] if result and result['total'] else 0
        
        return {
            'winners': [dict(w) for w in winners],
            'total_winners': len(winners),
            'total_prize': total_prize
        }

def add_fake_players():
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT session_id FROM game_sessions WHERE status = 'waiting' ORDER BY start_time DESC LIMIT 1")
        game = cursor.fetchone()
        
        if not game:
            session_id = random.randint(100, 999)
            cursor.execute('''
                INSERT INTO game_sessions (session_id, start_time, status)
                VALUES (?, ?, 'waiting')
            ''', (session_id, datetime.now()))
            game = {'session_id': session_id}
        
        cursor.execute("SELECT COUNT(*) as count FROM entries WHERE session_id = ?", (game['session_id'],))
        result = cursor.fetchone()
        current_count = result['count'] if result else 0
        
        if current_count >= TOTAL_PLAYERS:
            return False, "Game already has 20 players"
        
        fake_names = ['Lucky', 'Winner', 'Jackpot', 'Fortune', 'Victory', 'Champion', 'Star', 'Ace', 'King', 'Queen']
        added = 0
        
        for i in range(TOTAL_PLAYERS - current_count):
            fake_name = f"{fake_names[i % len(fake_names)]}_{random.randint(100, 999)}"
            fake_id = random.randint(100000, 999999)
            ticket = random.randint(1000, 9999)
            
            cursor.execute("INSERT OR IGNORE INTO users (user_id, username, is_demo) VALUES (?, ?, 1)", (fake_id, fake_name))
            
            cursor.execute('''
                INSERT INTO entries (session_id, user_id, username, ticket_number, entry_time, payment_status)
                VALUES (?, ?, ?, ?, ?, 'demo')
            ''', (game['session_id'], fake_id, fake_name, ticket, datetime.now()))
            
            cursor.execute("UPDATE game_sessions SET total_collected = total_collected + ?, total_players = total_players + 1 WHERE session_id = ?", (ENTRY_FEE, game['session_id']))
            added += 1
        
        # Check if game is now full
        cursor.execute("SELECT COUNT(*) as count FROM entries WHERE session_id = ?", (game['session_id'],))
        result = cursor.fetchone()
        if result['count'] >= TOTAL_PLAYERS:
            play_game(game['session_id'])
        
        return True, added

def reset_all_data():
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM winners")
        cursor.execute("DELETE FROM entries")
        cursor.execute("DELETE FROM payment_requests")
        cursor.execute("DELETE FROM game_sessions")
        cursor.execute("DELETE FROM users")
        
        cursor.execute("DELETE FROM sqlite_sequence")
        
        new_session_id = random.randint(100, 999)
        cursor.execute('''
            INSERT INTO game_sessions (session_id, start_time, status)
            VALUES (?, ?, 'waiting')
        ''', (new_session_id, datetime.now()))
        
        return True

def add_demo_user(user_id, username):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (user_id, username, is_demo, demo_balance) VALUES (?, ?, 1, 300)", (user_id, username))
        return True

if __name__ == "__main__":
    init_database()
    print("Database ready!")