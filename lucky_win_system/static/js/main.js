// static/js/main.js - Real Database Version
let gameData = {
    currentSessionId: null,
    playerCount: 0,
    isSpinning: false,
    spinAnimationId: null,
    currentRotation: 0,
    spinVelocity: 12,
    spinDecay: 0.98,
    minVelocity: 0.5
};

// ========== DASHBOARD FUNCTIONS ==========
async function loadDashboard() {
    try {
        // Load game stats
        const statsRes = await fetch('/api/game_stats');
        const stats = await statsRes.json();
        
        document.getElementById('totalGames').innerText = stats.total_games;
        document.getElementById('totalProfit').innerText = stats.total_profit.toLocaleString() + ' Birr';
        document.getElementById('totalPlayers').innerText = stats.total_players;
        document.getElementById('currentPlayers').innerText = stats.current_players + '/20';
        
        const percent = (stats.current_players / 20) * 100;
        const progressBar = document.getElementById('gameProgress');
        if (progressBar) {
            progressBar.style.width = percent + '%';
            progressBar.innerText = stats.current_players + '/20 Players';
        }
        
        document.getElementById('playerCount').innerText = stats.current_players;
        document.getElementById('progressPercent').innerText = Math.round(percent) + '%';
        
        const needed = 20 - stats.current_players;
        document.getElementById('playersNeeded').innerText = needed > 0 ? `Need ${needed} more players` : 'Game ready! Click START SPIN!';
        
        // Load current game
        const gameRes = await fetch('/api/current_game');
        const game = await gameRes.json();
        
        gameData.currentSessionId = game.session_id;
        gameData.playerCount = game.player_count;
        document.getElementById('luckyNumber').innerText = game.lucky_number || '--';
        
        // Update players grid
        let playersHtml = '<div class="row">';
        if (game.players && game.players.length > 0) {
            game.players.forEach((p, i) => {
                playersHtml += `
                    <div class="col-md-3 col-sm-6 mb-2">
                        <div class="player-card">
                            <div class="d-flex align-items-center">
                                <div class="player-avatar">${(p.username.charAt(0) || 'U').toUpperCase()}</div>
                                <div>
                                    <strong>${i+1}. @${p.username}</strong>
                                    <br><small>Ticket #${p.ticket_number || 'N/A'}</small>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
        } else {
            playersHtml = `
                <div class="col-12 text-center py-4">
                    <p>No players yet</p>
                    <button class="btn-success-custom" onclick="addFakePlayers()">➕ Add 20 Fake Players</button>
                </div>
            `;
        }
        playersHtml += '</div>';
        document.getElementById('playersGrid').innerHTML = playersHtml;
        
        // Show/hide spin container
        const spinContainer = document.getElementById('spinContainer');
        if (spinContainer) {
            spinContainer.style.display = game.player_count >= 20 ? 'block' : 'none';
        }
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// ========== PLAYERS PAGE ==========
async function loadPlayers() {
    try {
        const res = await fetch('/api/players_data');
        const data = await res.json();
        
        document.getElementById('totalPlayersStat').innerText = data.total_players;
        document.getElementById('totalWonStat').innerText = data.total_won.toLocaleString() + ' Birr';
        document.getElementById('totalSpentStat').innerText = data.total_spent.toLocaleString() + ' Birr';
        document.getElementById('activePlayersStat').innerText = data.active_players;
        
        let html = '';
        data.players.forEach((p, i) => {
            const profit = p.total_won - p.total_spent;
            html += `
                <tr>
                    <td>${i+1}</td>
                    <td><strong>@${p.username || 'Unknown'}</strong></td>
                    <td><code>${p.user_id || p.id}</code></td>
                    <td><span class="badge bg-success">${p.balance || 0} Birr</span></td>
                    <td>${p.total_spent || 0} Birr</td>
                    <td class="text-success">${p.total_won || 0} Birr</td>
                    <td class="${profit >= 0 ? 'text-success' : 'text-danger'}">${profit} Birr</td>
                    <td>${p.games_played || 0}</td>
                    <td><small>${p.joined_date ? p.joined_date.slice(0, 10) : '-'}</small></td>
                </tr>
            `;
        });
        document.getElementById('playersTableBody').innerHTML = html;
    } catch (error) {
        console.error('Error loading players:', error);
    }
}

// ========== GAMES PAGE ==========
async function loadGames() {
    try {
        const res = await fetch('/api/games_data');
        const data = await res.json();
        
        document.getElementById('totalGamesStat').innerText = data.total_games;
        document.getElementById('totalCollectedStat').innerText = data.total_collected.toLocaleString() + ' Birr';
        document.getElementById('totalPaidStat').innerText = data.total_paid.toLocaleString() + ' Birr';
        document.getElementById('totalProfitStat').innerText = data.total_profit.toLocaleString() + ' Birr';
        
        let html = '';
        data.games.forEach(g => {
            const paidPct = (g.total_paid / g.total_collected) * 100;
            const profitPct = (g.admin_profit / g.total_collected) * 100;
            html += `
                <div class="col-md-6 mb-3">
                    <div class="game-card" onclick="showGameDetails(${g.session_id})">
                        <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);color:white;padding:15px;display:flex;justify-content:space-between">
                            <span>🎮 Game #${g.session_id}</span><span class="badge bg-success">${g.player_count || 20} players</span>
                        </div>
                        <div style="padding:15px">
                            <div class="progress mb-3" style="height:30px">
                                <div class="progress-bar bg-success" style="width:${paidPct}%">Paid ${paidPct.toFixed(1)}%</div>
                                <div class="progress-bar bg-warning" style="width:${profitPct}%">Profit ${profitPct.toFixed(1)}%</div>
                            </div>
                            <div class="row text-center">
                                <div class="col-4"><small>Collected</small><br><strong>${g.total_collected} Birr</strong></div>
                                <div class="col-4"><small>Paid</small><br><strong>${g.total_paid} Birr</strong></div>
                                <div class="col-4"><small>Profit</small><br><strong>${g.admin_profit} Birr</strong></div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        document.getElementById('gamesGrid').innerHTML = html || '<div class="col-12 text-center py-4">No games yet</div>';
    } catch (error) {
        console.error('Error loading games:', error);
    }
}

async function showGameDetails(sessionId) {
    try {
        const res = await fetch(`/api/game_details/${sessionId}`);
        const game = await res.json();
        
        let html = `
            <h6>Game #${game.session_id}</h6><hr>
            <div class="row mb-3">
                <div class="col-6"><strong>Started:</strong><br>${game.start_time}</div>
                <div class="col-6"><strong>Ended:</strong><br>${game.end_time || 'In Progress'}</div>
            </div>
            <div class="row mb-3">
                <div class="col-4"><div class="alert alert-success text-center">💰 ${game.total_collected} Birr</div></div>
                <div class="col-4"><div class="alert alert-danger text-center">💸 ${game.total_paid} Birr</div></div>
                <div class="col-4"><div class="alert alert-warning text-center">💼 ${game.admin_profit} Birr</div></div>
            </div>
            <h6>🏆 Winners</h6>
            <div class="row mb-3">
        `;
        
        if (game.winners && game.winners.length) {
            game.winners.forEach(w => {
                const icon = w.rank === 1 ? '🥇' : w.rank === 2 ? '🥈' : '🥉';
                html += `<div class="col-md-4 text-center"><div style="background:#f8f9fa;padding:10px;border-radius:10px">${icon} <strong>@${w.username}</strong><br>+${w.prize_amount} Birr</div></div>`;
            });
        } else {
            html += '<div class="col-12 text-center">No winners recorded</div>';
        }
        
        html += `</div><hr><h6>Players (${game.players?.length || 0}/20)</h6><div class="row">`;
        if (game.players) {
            game.players.forEach(p => {
                html += `<div class="col-md-3"><i class="bi bi-person-circle"></i> @${p.username}</div>`;
            });
        }
        html += `</div>`;
        
        document.getElementById('gameModalBody').innerHTML = html;
        new bootstrap.Modal(document.getElementById('gameModal')).show();
    } catch (error) {
        console.error('Error loading game details:', error);
    }
}

// ========== WINNERS PAGE ==========
async function loadWinners() {
    try {
        const res = await fetch('/api/winners_data');
        const data = await res.json();
        
        document.getElementById('totalWinnersStat').innerText = data.total_winners;
        document.getElementById('totalPrizeStat').innerText = data.total_prize.toLocaleString() + ' Birr';
        document.getElementById('firstPlaceStat').innerText = data.first_place_count;
        document.getElementById('avgPrizeStat').innerText = data.avg_prize.toLocaleString() + ' Birr';
        
        let html = '';
        data.winners.forEach((w, i) => {
            const icon = w.rank === 1 ? '🥇' : w.rank === 2 ? '🥈' : '🥉';
            html += `
                <tr>
                    <td>${i+1}</td>
                    <td><strong>@${w.username}</strong></td>
                    <td><span class="badge ${w.rank === 1 ? 'bg-warning' : w.rank === 2 ? 'bg-secondary' : 'bg-danger'}">${icon} ${w.rank}${w.rank === 1 ? 'st' : w.rank === 2 ? 'nd' : 'rd'}</span></td>
                    <td class="text-success fw-bold">${w.prize_amount} Birr</td>
                    <td><span class="badge bg-info">#${w.session_id}</span></td>
                    <td><small>${w.paid_time ? w.paid_time.slice(0, 16) : '-'}</small></td>
                </tr>
            `;
        });
        document.getElementById('winnersTableBody').innerHTML = html;
    } catch (error) {
        console.error('Error loading winners:', error);
    }
}

// ========== PAYMENTS PAGE ==========
let currentStatus = 'pending';

async function loadPayments() {
    try {
        const res = await fetch(`/api/payments_data?status=${currentStatus}`);
        const data = await res.json();
        
        document.getElementById('pendingCount').innerText = data.pending;
        document.getElementById('confirmedCount').innerText = data.confirmed;
        document.getElementById('rejectedCount').innerText = data.rejected;
        document.getElementById('totalAmount').innerText = data.total_amount.toLocaleString() + ' Birr';
        
        let html = '';
        data.payments.forEach(p => {
            const statusClass = p.status === 'pending' ? 'warning' : p.status === 'confirmed' ? 'success' : 'danger';
            html += `
                <tr class="table-${statusClass}">
                    <td><strong>@${p.username || p.sender_name}</strong></td>
                    <td><span class="badge bg-success">${p.amount} Birr</span></td>
                    <td><code>${p.transaction_ref}</code></td>
                    <td>${p.sender_phone || '-'}</td>
                    <td><small>${p.requested_at}</small></td>
                    <td><span class="badge bg-${statusClass}">${p.status}</span></td>
                    <td>
                        ${p.status === 'pending' ? `
                            <button class="btn btn-success btn-sm me-1" onclick="confirmPayment(${p.id})">Confirm</button>
                            <button class="btn btn-danger btn-sm" onclick="rejectPayment(${p.id})">Reject</button>
                        ` : '-'}
                    </td>
                </tr>
            `;
        });
        document.getElementById('paymentsTableBody').innerHTML = html || '<tr><td colspan="7" class="text-center py-4">No payments found</td></tr>';
    } catch (error) {
        console.error('Error loading payments:', error);
    }
}

async function confirmPayment(id) {
    if (!confirm('Confirm this payment?')) return;
    await fetch('/api/confirm_payment', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id }) });
    loadPayments();
    alert('✅ Payment confirmed!');
}

async function rejectPayment(id) {
    const reason = prompt('Reason for rejection:');
    if (!reason) return;
    await fetch('/api/reject_payment', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id }) });
    loadPayments();
    alert('❌ Payment rejected!');
}

function setPaymentStatus(status) {
    currentStatus = status;
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    if (event && event.target) event.target.classList.add('active');
    loadPayments();
}

// ========== GAME ACTIONS ==========
async function addFakePlayers() {
    if (!confirm('Add 20 fake players to test?')) return;
    
    const btn = event.target;
    const originalText = btn.innerText;
    btn.innerText = 'Adding...';
    btn.disabled = true;
    
    const res = await fetch('/api/add_fake_players', { method: 'POST' });
    const data = await res.json();
    
    if (data.success) {
        alert(`✅ ${data.added} fake players added!`);
        location.reload();
    } else {
        alert('❌ Error: ' + data.error);
    }
    btn.innerText = originalText;
    btn.disabled = false;
}

async function resetDatabase() {
    const confirmText = prompt('⚠️ Type "RESET" to delete all data:');
    if (confirmText !== 'RESET') return;
    
    await fetch('/api/reset_database', { method: 'POST' });
    alert('✅ Database reset!');
    location.reload();
}

// ========== SPIN FUNCTIONS ==========
function startSpin() {
    if (gameData.isSpinning) return;
    if (gameData.playerCount < 20) {
        alert(`Need 20 players! Current: ${gameData.playerCount}`);
        return;
    }
    
    gameData.isSpinning = true;
    gameData.spinVelocity = 12;
    gameData.currentRotation = 0;
    
    const wheel = document.getElementById('wheel');
    
    function animate() {
        if (!gameData.isSpinning) return;
        
        gameData.currentRotation += gameData.spinVelocity;
        gameData.spinVelocity *= gameData.spinDecay;
        wheel.style.transform = `rotate(${gameData.currentRotation}deg)`;
        
        if (gameData.spinVelocity > gameData.minVelocity) {
            gameData.spinAnimationId = requestAnimationFrame(animate);
        } else {
            stopSpinAndDraw();
        }
    }
    
    gameData.spinAnimationId = requestAnimationFrame(animate);
    document.getElementById('startBtn').style.display = 'none';
    document.getElementById('stopBtn').style.display = 'inline-block';
}

async function stopSpinAndDraw() {
    if (gameData.spinAnimationId) cancelAnimationFrame(gameData.spinAnimationId);
    gameData.isSpinning = false;
    
    document.getElementById('startBtn').style.display = 'inline-block';
    document.getElementById('stopBtn').style.display = 'none';
    
    const res = await fetch('/api/draw_winners', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: gameData.currentSessionId })
    });
    const data = await res.json();
    
    if (data.winners) {
        showWinnersModal(data.winners, data.total_collected, data.total_paid, data.admin_profit);
        setTimeout(() => location.reload(), 4000);
    } else {
        alert('Error: ' + data.error);
    }
}

function stopSpin() {
    if (!gameData.isSpinning) return;
    gameData.spinVelocity = Math.max(gameData.spinVelocity, 3);
    const interval = setInterval(() => {
        if (gameData.spinVelocity <= gameData.minVelocity) {
            clearInterval(interval);
            stopSpinAndDraw();
        } else {
            gameData.spinVelocity *= 0.92;
        }
    }, 50);
}

function showWinnersModal(winners, totalCollected, totalPaid, adminProfit) {
    let html = `<div style="text-align:center"><div style="font-size:48px">🎉✨🏆✨🎉</div><h2>WINNERS!</h2><div class="row">`;
    winners.forEach(w => {
        const color = w.rank === 1 ? '#ffd700' : w.rank === 2 ? '#c0c0c0' : '#cd7f32';
        html += `
            <div class="col-md-4">
                <div style="background:${color};border-radius:20px;padding:25px;color:${w.rank===1?'#000':'#fff'}">
                    <div style="font-size:48px">${w.rank===1?'🥇':w.rank===2?'🥈':'🥉'}</div>
                    <h3>${w.rank===1?'1st':w.rank===2?'2nd':'3rd'}</h3>
                    <h4>@${w.username}</h4>
                    <h5>Ticket #${w.ticket}</h5>
                    <h2>+${w.prize} Birr</h2>
                </div>
            </div>
        `;
    });
    html += `</div><hr><div class="row"><div class="col-md-4"><div class="alert alert-info">💰 Total: ${totalCollected} Birr</div></div><div class="col-md-4"><div class="alert alert-success">💸 Paid: ${totalPaid} Birr</div></div><div class="col-md-4"><div class="alert alert-warning">💼 Profit: ${adminProfit} Birr</div></div></div></div>`;
    
    document.getElementById('winnerModalBody').innerHTML = html;
    new bootstrap.Modal(document.getElementById('winnerModal')).show();
    
    if (typeof confetti === 'function') {
        confetti({ particleCount: 300, spread: 100, origin: { y: 0.6 } });
        setTimeout(() => confetti({ particleCount: 200, spread: 70, origin: { y: 0.5 } }), 500);
    }
}

// ========== INITIALIZE ==========
document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;
    if (path === '/dashboard') loadDashboard();
    else if (path === '/players') loadPlayers();
    else if (path === '/games') loadGames();
    else if (path === '/winners') loadWinners();
    else if (path === '/payments') loadPayments();
    
    // Auto refresh every 10 seconds
    setInterval(() => {
        const p = window.location.pathname;
        if (p === '/dashboard') loadDashboard();
        else if (p === '/players') loadPlayers();
        else if (p === '/games') loadGames();
        else if (p === '/winners') loadWinners();
        else if (p === '/payments') loadPayments();
    }, 10000);
});

// Update the confirmPayment and rejectPayment functions

async function confirmPayment(paymentId) {
    if (!confirm('✅ Confirm this payment?\n\nUser will be added to the game immediately.')) return;
    
    const btn = event.target;
    const originalText = btn.innerText;
    btn.innerText = 'Confirming...';
    btn.disabled = true;
    
    try {
        const res = await fetch('/api/confirm_payment_admin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ payment_id: paymentId })
        });
        const data = await res.json();
        
        if (data.success) {
            alert('✅ ' + data.message);
            loadPayments();
            // Update dashboard stats
            if (window.location.pathname === '/dashboard') loadDashboard();
        } else {
            alert('❌ Error: ' + data.error);
        }
    } catch (error) {
        alert('❌ Error confirming payment');
    }
    
    btn.innerText = originalText;
    btn.disabled = false;
}

async function rejectPayment(paymentId) {
    const reason = prompt('❌ Reason for rejection:');
    if (!reason) return;
    
    if (!confirm('Reject this payment?')) return;
    
    const btn = event.target;
    const originalText = btn.innerText;
    btn.innerText = 'Rejecting...';
    btn.disabled = true;
    
    try {
        const res = await fetch('/api/reject_payment_admin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ payment_id: paymentId, reason: reason })
        });
        const data = await res.json();
        
        if (data.success) {
            alert('❌ Payment rejected');
            loadPayments();
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Error rejecting payment');
    }
    
    btn.innerText = originalText;
    btn.disabled = false;
}

// Make functions global
window.addFakePlayers = addFakePlayers;
window.resetDatabase = resetDatabase;
window.startSpin = startSpin;
window.stopSpin = stopSpin;
window.confirmPayment = confirmPayment;
window.rejectPayment = rejectPayment;
window.setPaymentStatus = setPaymentStatus;
window.showGameDetails = showGameDetails;