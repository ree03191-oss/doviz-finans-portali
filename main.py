import sqlite3
import os
import io
import requests
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for, make_response
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from xhtml2pdf import pisa

app = Flask(__name__)

# CSRF ve Session Gizli Anahtarı
app.config['SECRET_KEY'] = 'xxsd45rrt092545expertuuiklop'
csrf = CSRFProtect(app)

# OpenAI Entegrasyonu (İsteğe Bağlı)
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "GECICI_KEY"))
except ImportError:
    client = None

DB_NAME = 'finans.db'
# --- VERİTABANI KURULUMU ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            asset_code TEXT NOT NULL,
            amount REAL NOT NULL,
            buy_price REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # İşlem Geçmişi Tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            asset_code TEXT NOT NULL,
            type TEXT NOT NULL, -- 'ALIM' veya 'SATIM'
            amount REAL NOT NULL,
            price REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# --- CANLI KUR VE HABER SERVİSİ ---
def kurlari_al():
    usd_try, eur_try, gram_altin = 34.20, 37.50, 3050.0
    btc_usd, eth_usd = 65000.0, 3500.0

    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        res = requests.get("https://finans.truncgil.com/today.json", headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if 'USD' in data and 'Satış' in data['USD']:
                usd_try = float(data['USD']['Satış'].replace('.', '').replace(',', '.'))
            if 'EUR' in data and 'Satış' in data['EUR']:
                eur_try = float(data['EUR']['Satış'].replace('.', '').replace(',', '.'))
            if 'gram-altin' in data and 'Satış' in data['gram-altin']:
                gram_altin = float(data['gram-altin']['Satış'].replace('.', '').replace(',', '.'))
    except Exception as e:
        print(f"Döviz/Altın Çekme Hatası: {e}")

    try:
        btc_res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=3)
        if btc_res.status_code == 200:
            btc_usd = float(btc_res.json()['price'])

        eth_res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT", timeout=3)
        if eth_res.status_code == 200:
            eth_usd = float(eth_res.json()['price'])
    except Exception as e:
        print(f"Kripto Çekme Hatası: {e}")

    return {
        'USD': round(usd_try, 2),
        'EUR': round(eur_try, 2),
        'GA': round(gram_altin, 2),
        'BTC': round(btc_usd * usd_try, 2),
        'ETH': round(eth_usd * usd_try, 2)
    }

def haberleri_al():
    return [
        {"title": "Merkez Bankaları Faiz Kararlarını Açıklamaya Hazırlanıyor", "time": "10 dk önce"},
        {"title": "Bitcoin 65.000$ Direncini Test Ediyor", "time": "30 dk önce"},
        {"title": "Altın Fiyatlarında Küresel Piyasa Hareketliliği", "time": "1 saat önce"}
    ]

# --- AI ANALİZ MOTORU ---
def ai_analiz_ureti(user_prompt, user_id):
    kurlar = kurlari_al()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT asset_code, amount, buy_price FROM portfolio WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()

    portfoy_ozet, toplam_deger, toplam_maliyet = [], 0, 0
    for code, amount, buy_price in rows:
        canli_fiyat = kurlar.get(code, 0)
        mevcut_val = amount * canli_fiyat
        toplam_deger += mevcut_val
        toplam_maliyet += amount * buy_price
        portfoy_ozet.append(f"{code}: {amount} Adet, Canlı Değer: ₺{mevcut_val:.2f}")

    toplam_kz = toplam_deger - toplam_maliyet
    p_str = "; ".join(portfoy_ozet) if portfoy_ozet else "Portföy boş."

    system_context = f"""
    Sen finansal uzmansın.
    Piyasalar: USD={kurlar['USD']}, EUR={kurlar['EUR']}, Altın={kurlar['GA']} TL, BTC={kurlar['BTC']} TL.
    Kullanıcı Portföyü: {p_str}. Toplam Değer: ₺{toplam_deger:.2f}, Kâr/Zarar: ₺{toplam_kz:.2f}.
    Soruya doğrudan, mantıklı ve finansal açıdan objektif yanıt ver.
    """

    if client and os.environ.get("OPENAI_API_KEY") and os.environ.get("OPENAI_API_KEY") != "YOUR_OPENAI_API_KEY":
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": system_context}, {"role": "user", "content": user_prompt}],
                max_tokens=300
            )
            return f"🤖 **AI Asistanı:**\n\n{response.choices[0].message.content.strip()}"
        except Exception as e:
            print(f"OpenAI Hatası: {e}")

    return f"🤖 **AI Asistanı:** Sorunuz ('{user_prompt}') analiz edildi. Portföyünüzün mevcut toplam değeri ₺{toplam_deger:.2f} seviyesindedir. Yatırımlarınızı çeşitlendirerek riski dağıtmanızı öneririm."

# --- HTML ARAYÜZÜ ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gelişmiş Finans & Kripto Portalı</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg-color: #121212; --card-bg: #1e1e1e; --text-color: #ffffff;
            --subtext-color: #a0a0a0; --border-color: #333333; --input-bg: #2a2a2a;
        }
        body.light-mode {
            --bg-color: #f4f6f9; --card-bg: #ffffff; --text-color: #1a1a1a;
            --subtext-color: #666666; --border-color: #e0e0e0; --input-bg: #f0f0f0;
        }
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: var(--bg-color); color: var(--text-color); margin: 0; padding: 20px; transition: 0.3s; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        h1 { color: #00e676; margin: 0; font-size: 24px; }
        .nav-btns { display: flex; gap: 10px; align-items: center; }
        
        .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 25px; }
        .card { background: var(--card-bg); border: 1px solid var(--border-color); padding: 15px; border-radius: 10px; text-align: center; }
        .card h3 { margin: 0; font-size: 14px; color: var(--subtext-color); }
        .card .price { font-size: 22px; font-weight: bold; color: #00e676; margin: 8px 0; }

        .dashboard-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 25px; }
        @media(max-width: 900px) { .dashboard-grid { grid-template-columns: 1fr; } }

        .section { background: var(--card-bg); border: 1px solid var(--border-color); padding: 20px; border-radius: 10px; margin-bottom: 25px; }
        .form-group { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 15px; }
        input, select, button { padding: 10px; border-radius: 6px; border: 1px solid var(--border-color); background: var(--input-bg); color: var(--text-color); }
        input { flex: 1; min-width: 120px; }
        button { background: #00e676; color: #121212; font-weight: bold; cursor: pointer; border: none; }
        button:hover { opacity: 0.9; }
        .btn-danger { background: #ff5252; color: white; }
        .btn-blue { background: #29b6f6; color: white; }

        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 12px; border-bottom: 1px solid var(--border-color); text-align: left; }
        th { background: var(--input-bg); color: #00e676; }
        
        .auth-box { max-width: 400px; margin: 80px auto; background: var(--card-bg); border: 1px solid var(--border-color); padding: 30px; border-radius: 12px; }
        .profit { color: #00e676; font-weight: bold; } .loss { color: #ff5252; font-weight: bold; }

        .chat-box { height: 200px; overflow-y: auto; background: var(--input-bg); padding: 10px; border-radius: 8px; margin-bottom: 10px; border: 1px solid var(--border-color); }
        .chat-msg { margin-bottom: 10px; white-space: pre-line; font-size: 14px; }
        .chat-user { color: #29b6f6; font-weight: bold; }
        .chat-ai { color: #00e676; }

        footer { text-align: center; font-size: 12px; color: var(--subtext-color); margin-top: 30px; }
        footer a { color: #00e676; text-decoration: none; margin: 0 10px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        {% if not user %}
        <div class="auth-box">
            <h2 style="color:#00e676; text-align:center;">🔐 Finans Portalı</h2>
            {% if err %}<p style="color:#ff5252; text-align:center;">{{ err }}</p>{% endif %}
            <form method="POST" action="/login">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                <div style="display:flex; flex-direction:column; gap:12px;">
                    <input type="text" name="username" placeholder="Kullanıcı Adı" required>
                    <input type="password" name="password" placeholder="Şifre" required>
                    <button type="submit">Giriş Yap</button>
                    <button type="submit" name="register" value="1" class="btn-blue">Kayıt Ol</button>
                </div>
            </form>
        </div>
        {% else %}
        <div class="header-bar">
            <h1>📊 Canlı Finans & Kripto Portalı</h1>
            <div class="nav-btns">
                <button onclick="temaDegistir()">🌓 Tema</button>
                <select id="paraBirimi" onchange="portfoyGetir()" style="width: auto;">
                    <option value="TRY">₺ TRY</option>
                    <option value="USD">$ USD</option>
                    <option value="EUR">€ EUR</option>
                </select>
                <a href="/download/pdf"><button class="btn-blue">📄 PDF İndir</button></a>
                <a href="/logout"><button class="btn-danger">Çıkış</button></a>
            </div>
        </div>

        <div class="cards">
            <div class="card"><h3>💵 Dolar (USD)</h3><div class="price" id="c-USD">₺{{ kurlar['USD'] }}</div></div>
            <div class="card"><h3>💶 Euro (EUR)</h3><div class="price" id="c-EUR">₺{{ kurlar['EUR'] }}</div></div>
            <div class="card"><h3>🪙 Gram Altın</h3><div class="price" id="c-GA">₺{{ kurlar['GA'] }}</div></div>
            <div class="card"><h3>₿ Bitcoin (BTC)</h3><div class="price" id="c-BTC">₺{{ kurlar['BTC'] }}</div></div>
            <div class="card"><h3>Ξ Ethereum (ETH)</h3><div class="price" id="c-ETH">₺{{ kurlar['ETH'] }}</div></div>
        </div>

        <div class="dashboard-grid">
            <div class="section" style="margin-bottom:0;">
                <h2 style="color:#00e676; margin-top:0;">💼 Portföyüm</h2>
                <div class="form-group">
                    <select id="vKod">
                        <option value="USD">Dolar (USD)</option>
                        <option value="EUR">Euro (EUR)</option>
                        <option value="GA">Gram Altın</option>
                        <option value="BTC">Bitcoin (BTC)</option>
                        <option value="ETH">Ethereum (ETH)</option>
                    </select>
                    <input type="number" id="vMiktar" placeholder="Miktar" step="any">
                    <input type="number" id="vAlis" placeholder="Alış Fiyatı (TL)" step="any">
                    <button onclick="dbVarlikEkle()">Varlık Ekle</button>
                </div>

                <table>
                    <thead>
                        <tr><th>Varlık</th><th>Miktar</th><th>Alış F.</th><th>Canlı F.</th><th>Mevcut Değer</th><th>K/Z</th><th>İşlem</th></tr>
                    </thead>
                    <tbody id="portfoyBody"></tbody>
                </table>
            </div>

            <div class="section" style="margin-bottom:0;">
                <h2 style="color:#00e676; margin-top:0;">📈 Portföy Dağılımı</h2>
                <div style="position: relative; height:220px; width:100%;">
                    <canvas id="portfolioChart"></canvas>
                </div>
            </div>
        </div>

        <!-- AI RISK VE ASİSTAN -->
        <div class="section">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h2 style="color:#00e676; margin-top:0;">🤖 AI Risk Analizi & Asistan</h2>
                <button onclick="otomatikRiskAnalizi()" class="btn-blue">⚡ Otomatik Risk Analizi Yap</button>
            </div>
            <div class="chat-box" id="chatBox">
                <div class="chat-msg chat-ai">🤖 AI: Merhaba! Bana finansal sorular sorabilir veya yukarıdaki butonla otomatik risk analizi alabilirsiniz.</div>
            </div>
            <div class="form-group" style="margin-bottom:0;">
                <input type="text" id="aiInput" placeholder="Sorunuzu yazın..." onkeypress="if(event.key==='Enter') aiSoruSor()">
                <button onclick="aiSoruSor()" class="btn-blue">Gönder</button>
            </div>
        </div>

        <div class="dashboard-grid">
            <!-- İŞLEM GEÇMİŞİ -->
            <div class="section" style="margin-bottom:0;">
                <h2 style="color:#00e676; margin-top:0;">📜 Al/Sat İşlem Geçmişi</h2>
                <table>
                    <thead>
                        <tr><th>Tarih</th><th>İşlem</th><th>Varlık</th><th>Miktar</th><th>Fiyat</th></tr>
                    </thead>
                    <tbody id="islemBody"></tbody>
                </table>
            </div>

            <!-- ANLIK HABER AKIŞI -->
            <div class="section" style="margin-bottom:0;">
                <h2 style="color:#00e676; margin-top:0;">📰 Anlık Finans Haberleri</h2>
                <div id="haberAkisi">
                    {% for haber in haberler %}
                    <div style="border-bottom: 1px solid var(--border-color); padding: 8px 0;">
                        <div style="font-size:14px; font-weight:bold;">{{ haber.title }}</div>
                        <div style="font-size:11px; color:var(--subtext-color);">{{ haber.time }}</div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
        {% endif %}

        <footer>
            <p>© 2026 Canlı Finans Portalı. Tüm Hakları Saklıdır.</p>
        </footer>
    </div>

    <script>
        let KURLAR = {{ kurlar | tojson if kurlar else '{}' }};
        let myChart = null;

        function temaDegistir() {
            document.body.classList.toggle('light-mode');
        }

        function initChart(labels = [], data = []) {
            const ctx = document.getElementById('portfolioChart');
            if(!ctx) return;
            if (myChart) myChart.destroy();
            
            myChart = new Chart(ctx.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: ['#00e676', '#29b6f6', '#ffca28', '#ab47bc', '#ff7043'],
                        borderWidth: 1
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false }
            });
        }

        async function portfoyGetir() {
            const res = await fetch('/api/portfolio');
            if(!res.ok) return;
            const data = await res.json();
            const tbody = document.getElementById('portfoyBody');
            if(!tbody) return;
            tbody.innerHTML = '';

            const pb = document.getElementById('paraBirimi').value;
            let carpan = 1;
            let sembol = '₺';

            if(pb === 'USD') { carpan = 1 / KURLAR['USD']; sembol = '$'; }
            if(pb === 'EUR') { carpan = 1 / KURLAR['EUR']; sembol = '€'; }

            let chartLabels = [];
            let chartData = [];

            data.forEach(item => {
                const canlı = (KURLAR[item.code] || 0) * carpan;
                const alis = item.buy_price * carpan;
                const maliyet = item.amount * alis;
                const mevcut = item.amount * canlı;
                const kz = mevcut - maliyet;

                chartLabels.push(item.code);
                chartData.push(mevcut.toFixed(2));

                tbody.innerHTML += `
                    <tr>
                        <td><strong>${item.code}</strong></td>
                        <td>${item.amount}</td>
                        <td>${sembol}${alis.toFixed(2)}</td>
                        <td>${sembol}${canlı.toFixed(2)}</td>
                        <td>${sembol}${mevcut.toFixed(2)}</td>
                        <td class="${kz >= 0 ? 'profit':'loss'}">${sembol}${kz.toFixed(2)}</td>
                        <td><button class="btn-danger" onclick="dbVarlikSil(${item.id}, '${item.code}', ${item.amount}, ${item.buy_price})">Sat/Sil</button></td>
                    </tr>
                `;
            });

            initChart(chartLabels, chartData);
            islemGecmisiGetir();
        }

        async function islemGecmisiGetir() {
            const res = await fetch('/api/transactions');
            if(!res.ok) return;
            const data = await res.json();
            const tbody = document.getElementById('islemBody');
            if(!tbody) return;
            tbody.innerHTML = data.map(t => `
                <tr>
                    <td><small>${t.timestamp}</small></td>
                    <td><span style="color:${t.type==='ALIM'?'#00e676':'#ff5252'}">${t.type}</span></td>
                    <td>${t.asset_code}</td>
                    <td>${t.amount}</td>
                    <td>₺${t.price}</td>
                </tr>
            `).join('');
        }

        async function dbVarlikEkle() {
            const code = document.getElementById('vKod').value;
            const amount = parseFloat(document.getElementById('vMiktar').value);
            const buy_price = parseFloat(document.getElementById('vAlis').value);

            if(!amount || !buy_price) return alert('Lütfen geçerli değer girin!');

            await fetch('/api/portfolio/add', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ code, amount, buy_price })
            });

            document.getElementById('vMiktar').value = '';
            document.getElementById('vAlis').value = '';
            portfoyGetir();
        }

        async function dbVarlikSil(id, code, amount, buy_price) {
            await fetch(`/api/portfolio/delete/${id}`, {
                method: 'DELETE',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ code, amount, buy_price })
            });
            portfoyGetir();
        }

        async function aiSoruSor() {
            const input = document.getElementById('aiInput');
            const query = input.value.trim();
            if(!query) return;

            const chatBox = document.getElementById('chatBox');
            chatBox.innerHTML += `<div class="chat-msg chat-user">👤 Siz: ${query}</div>`;
            input.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;

            const res = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ prompt: query })
            });

            if(res.ok) {
                const data = await res.json();
                chatBox.innerHTML += `<div class="chat-msg chat-ai">${data.response}</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        }

        function otomatikRiskAnalizi() {
            document.getElementById('aiInput').value = "Portföyümün risk durumunu otomatik analiz et ve çeşitlendirme tavsiyesi ver.";
            aiSoruSor();
        }

        {% if user %}
        portfoyGetir();
        {% endif %}
    </script>
</body>
</html>
"""

# --- FLASK ROUTE'LARI ---
@app.route('/')
def index():
    user = session.get('user')
    kurlar = kurlari_al()
    haberler = haberleri_al()
    return render_template_string(HTML_TEMPLATE, user=user, kurlar=kurlar, haberler=haberler)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    is_register = request.form.get('register')

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if is_register:
        try:
            hashed = generate_password_hash(password)
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
            conn.commit()
            session['user'] = username
            session['user_id'] = cursor.lastrowid
        except sqlite3.IntegrityError:
            conn.close()
            return render_template_string(HTML_TEMPLATE, err="Kullanıcı adı alınmış!", kurlar=kurlari_al(), haberler=haberleri_al())
    else:
        cursor.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if row and check_password_hash(row[1], password):
            session['user'] = username
            session['user_id'] = row[0]
        else:
            conn.close()
            return render_template_string(HTML_TEMPLATE, err="Hatalı kullanıcı adı veya şifre!", kurlar=kurlari_al(), haberler=haberleri_al())

    conn.close()
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- REST API ---
@app.route('/api/portfolio')
def get_portfolio():
    if 'user_id' not in session: return jsonify([])
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, asset_code, amount, buy_price FROM portfolio WHERE user_id = ?", (session['user_id'],))
    rows = cursor.fetchall()
    conn.close()
    return jsonify([{'id': r[0], 'code': r[1], 'amount': r[2], 'buy_price': r[3]} for r in rows])

@app.route('/api/portfolio/add', methods=['POST'])
def add_portfolio():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO portfolio (user_id, asset_code, amount, buy_price) VALUES (?, ?, ?, ?)",
                   (session['user_id'], data['code'], data['amount'], data['buy_price']))
    cursor.execute("INSERT INTO transactions (user_id, asset_code, type, amount, price) VALUES (?, ?, 'ALIM', ?, ?)",
                   (session['user_id'], data['code'], data['amount'], data['buy_price']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/api/portfolio/delete/<int:item_id>', methods=['DELETE'])
def delete_portfolio(item_id):
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    data = request.json or {}
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM portfolio WHERE id = ? AND user_id = ?", (item_id, session['user_id']))
    if 'code' in data:
        cursor.execute("INSERT INTO transactions (user_id, asset_code, type, amount, price) VALUES (?, ?, 'SATIM', ?, ?)",
                       (session['user_id'], data['code'], data['amount'], data['buy_price']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/api/transactions')
def get_transactions():
    if 'user_id' not in session: return jsonify([])
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT asset_code, type, amount, price, timestamp FROM transactions WHERE user_id = ? ORDER BY id DESC LIMIT 10", (session['user_id'],))
    rows = cursor.fetchall()
    conn.close()
    return jsonify([{'asset_code': r[0], 'type': r[1], 'amount': r[2], 'price': r[3], 'timestamp': r[4]} for r in rows])

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    if 'user_id' not in session: return jsonify({'response': 'Lütfen önce giriş yapın.'})
    data = request.json
    response_text = ai_analiz_ureti(data.get('prompt', ''), session['user_id'])
    return jsonify({'response': response_text})

# --- PDF İNDİRME SERVİSİ ---
@app.route('/download/pdf')
def download_pdf():
    if 'user_id' not in session: return redirect(url_for('index'))
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT asset_code, amount, buy_price FROM portfolio WHERE user_id = ?", (session['user_id'],))
    rows = cursor.fetchall()
    conn.close()

    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Helvetica, sans-serif; }}
            h1 {{ color: #00e676; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ border: 1px solid #333; padding: 8px; text-align: left; }}
            th {{ background-color: #f0f0f0; }}
        </style>
    </head>
    <body>
        <h1>Finans Portalı - Portföy Raporu</h1>
        <p><b>Kullanıcı:</b> {session['user']}</p>
        <table>
            <tr><th>Varlık</th><th>Miktar</th><th>Alış Fiyatı (TL)</th></tr>
    """
    for r in rows:
        html_content += f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>₺{r[2]}</td></tr>"
    
    if not rows:
        html_content += "<tr><td colspan='3'>Henüz kayıtlı varlık bulunmamaktadır.</td></tr>"

    html_content += "</table></body></html>"

    pdf_buffer = io.BytesIO()
    pisa.CreatePDF(io.StringIO(html_content), dest=pdf_buffer)
    
    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=portfoy_raporu.pdf'
    return response

if __name__ == '__main__':
    app.run(debug=True)