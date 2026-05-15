# app.py
from flask import Flask, render_template, session, redirect, url_for, request, jsonify
from config import *
from database import *

app = Flask(__name__)
app.secret_key = SECRET_KEY

init_database()

@app.context_processor
def inject_config():
    return {
        'APP_NAME': APP_NAME,
        'ENTRY_FEE': ENTRY_FEE,
        'TOTAL_PLAYERS': TOTAL_PLAYERS,
        'WINNER_PRIZES': WINNER_PRIZES,
        'PROFIT_PER_GAME': PROFIT_PER_GAME,
        'TOTAL_COLLECTED': TOTAL_COLLECTED,
        'TOTAL_PAID': TOTAL_PAID,
        'TELEBIRR_ACCOUNT': TELEBIRR_ACCOUNT,
        'CBE_ACCOUNT': CBE_ACCOUNT
    }

# ========== AUTHENTICATION ==========
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            session['admin_username'] = username
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ========== MAIN PAGES ==========
@app.route('/')
def index():
    if 'admin' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'admin' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/players')
def players():
    if 'admin' not in session:
        return redirect(url_for('login'))
    return render_template('players.html')

@app.route('/games')
def games():
    if 'admin' not in session:
        return redirect(url_for('login'))
    return render_template('games.html')

@app.route('/winners')
def winners():
    if 'admin' not in session:
        return redirect(url_for('login'))
    return render_template('winners.html')

@app.route('/payments')
def payments():
    if 'admin' not in session:
        return redirect(url_for('login'))
    return render_template('payments.html')

# ========== API ENDPOINTS ==========
@app.route('/api/game_stats')
def api_game_stats():
    return jsonify(get_game_stats())

@app.route('/api/game_status')
def api_game_status():
    return jsonify(get_game_status())

@app.route('/api/players_data')
def api_players_data():
    return jsonify(get_all_players())

@app.route('/api/games_data')
def api_games_data():
    return jsonify(get_all_games())

@app.route('/api/winners_data')
def api_winners_data():
    return jsonify(get_all_winners())

@app.route('/api/game_details/<int:session_id>')
def api_game_details(session_id):
    return jsonify(get_game_details(session_id))

@app.route('/api/payments_data')
def api_payments_data():
    status = request.args.get('status', 'pending')
    return jsonify(get_all_payments(status))

@app.route('/api/confirm_payment', methods=['POST'])
def api_confirm_payment():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    success, message = confirm_payment(data['payment_id'], session['admin_username'], data.get('note'))
    if success:
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'error': message})

@app.route('/api/reject_payment', methods=['POST'])
def api_reject_payment():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    reject_payment(data['payment_id'], session['admin_username'], data['reason'])
    return jsonify({'success': True})

@app.route('/api/add_fake_players', methods=['POST'])
def api_add_fake_players():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    success, result = add_fake_players()
    if success:
        return jsonify({'success': True, 'added': result})
    return jsonify({'success': False, 'error': result})

@app.route('/api/reset_database', methods=['POST'])
def api_reset_database():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    reset_all_data()
    return jsonify({'success': True})

@app.route('/api/add_demo_user', methods=['POST'])
def api_add_demo_user():
    data = request.json
    add_demo_user(data['user_id'], data['username'])
    return jsonify({'success': True})

if __name__ == '__main__':
    print("=" * 50)
    print(f"🎲 {APP_NAME}")
    print("=" * 50)
    print(f"URL: http://localhost:{PORT}")
    print(f"Login: {ADMIN_USERNAME} / {ADMIN_PASSWORD}")
    print(f"Entry Fee: {ENTRY_FEE} Birr")
    print(f"1st Prize: {WINNER_PRIZES[1]} Birr")
    print(f"2nd Prize: {WINNER_PRIZES[2]} Birr")
    print(f"3rd Prize: {WINNER_PRIZES[3]} Birr")
    print(f"House Profit: {PROFIT_PER_GAME} Birr")
    print("=" * 50)
    app.run(debug=DEBUG, host='0.0.0.0', port=PORT)