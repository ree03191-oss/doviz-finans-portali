import sqlite3
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import requests

app = Flask(__name__)
app.secret_key = 'finans_gizli_anahtar_key_2026'
DB_NAME = 'finans.db'

# --- VERİTABANI KURULUMU ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Kullanıcılar Tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # Portföy Tablosu
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
    
    conn.commit()
    conn.close()

init_db()

# --- GÜNCELLENMİŞ CANLI KUR SERVİSİ ---
def kurlari_al():
    usd_try, eur_try, gram_altin = 34.20, 37.50, 3050.0
    btc_usd, eth_usd = 65000.0, 3500.0

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

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
        else:
            ex_res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=3)
            if ex_res.status_code == 200:
                rates = ex_res.json().get('rates', {})
                usd_try = rates.get('TRY', 34.20)
                eur_rate = rates.get('EUR', 0.92)
                eur_try = usd_try / eur_rate if eur_rate else 37.50
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

# --- AKILLI FİNANSAL AI ENGINE ---
def ai_analiz_ureti(prompt, user_id):
    kurlar = kurlari_al()
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT asset_code, amount, buy_price FROM portfolio WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()

    portfoy_ozet = []
    toplam_deger = 0
    toplam_maliyet = 0

    for code, amount, buy_price in rows:
        canli_fiyat = kurlar.get(code, 0)
        mevcut_val = amount * canli_fiyat
        maliyet_val = amount * buy_price
        toplam_deger += mevcut_val
        toplam_maliyet += maliyet_val
        portfoy_ozet.append(f"{code}: {amount} adet (Deger: ₺{mevcut_val:.2f}, K/Z: ₺{mevcut_val - maliyet_val:.2f})")

    toplam_kz = toplam_deger - toplam_maliyet
    p_str = ", ".join(portfoy_ozet) if portfoy_ozet else "Portfoy boş."

    prompt_lower = prompt.lower()
    
    if "portföy" in prompt_lower or "durum" in prompt_lower or "nasıl" in prompt_lower:
        if not rows:
            return "💡 **AI Analizi:** Henüz portföyünüze varlık eklemediğiniz için analiz yapamıyorum. Lütfen önce portföyünüze ekleme yapın."
        
        rekomendasyon = "Portföyünüz dengeli görünüyor."
        if toplam_kz < 0:
            rekomendasyon = "Şu an zarardasınız. Volatilitesi yüksek kripto varlıkların oranını gözden geçirebilir veya kademeli alım (DCA) düşünebilirsiniz."
        else:
            rekomendasyon = "Kârdasınız! Kâr realizasyonu yapmayı veya riski dağıtmak için Altın/Döviz oranını korumayı düşünebilirsiniz."

        return (f"📊 **Portföy AI Analiz Özeti:**\n\n"
                f"• **Toplam Portföy Değeri:** ₺{toplam_deger:.2f}\n"
                f"• **Toplam Kâr/Zarar:** ₺{toplam_kz:.2f}\n"
                f"• **Varlıklar:** {p_str}\n\n"
                f"🤖 **AI Tavsiyesi:** {rekomendasyon}")

    elif "tavsiye" in prompt_lower or "öneri" in prompt_lower or "al" in prompt_lower:
        return (f"🤖 **AI Yatırım Stratejisi Tavsiyesi:**\n\n"
                f"1. **Çeşitlendirme:** Tek bir varlığa bağımlı kalmayın. Sepetinizde geleneksel güvenli limanlar (Gram Altın) ve dinamik varlıklar (BTC/ETH) dengeli olmalı.\n"
                f"2. **Mevcut Kurlar:** USD/TRY: ₺{kurlar['USD']}, Gram Altın: ₺{kurlar['GA']}.\n"
                f"3. **Risk Yönetimi:** Yatırımlarınızı tek seferde değil, zamana yayarak (DCA) yapmak piyasa dalgalanmalarından korur.")

    else:
        return (f"🤖 **Finans AI Asistanı:**\n\n"
                f"Sorunuzu tam anlayamadım ama işte anlık finansal özetiniz:\n"
                f"• Dolar: ₺{kurlar['USD']} | Euro: ₺{kurlar['EUR']}\n"
                f"• Gram Altın: ₺{kurlar['GA']}\n"
                f"• Bitcoin: ₺{kurlar['BTC']}\n\n"
                f"Bana *'Portföyüm nasıl?'*, *'Bana yatırım tavsiyesi ver'* veya *'Durum analizi yap'* gibi sorular sorabilirsiniz!")

# --- HTML ARAYÜZÜ ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gelişmiş Canlı Finans & Kripto Portalı</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg-color: #121212; --card-bg: #1e1e1e; --text-color: #ffffff;
            --subtext-color: #a0a0a0; --border-color: #333333; --input-bg: #2a2a2a;
        }
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: var(--bg-color); color: var(--text-color); margin: 0; padding: 20px; }
        .container { max-width: 1100px; margin: 0 auto; }
        .header-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        h1 { color: #00e676; margin: 0; font-size: 24px; }
        .nav-btns { display: flex; gap: 10px; align-items: center; }
        
        .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 25px; }
        .card { background: var(--card-bg); border: 1px solid var(--border-color); padding: 15px; border-radius: 10px; text-align: center; }
        .card h3 { margin: 0; font-size: 14px; color: var(--subtext-color); }
        .card .price { font-size: 22px; font-weight: bold; color: #00e676; margin: 8px 0; }

        .dashboard-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 25px; }
        @media(max-width: 768px) { .dashboard-grid { grid-template-columns: 1fr; } }

        .section { background: var(--card-bg); border: 1px solid var(--border-color); padding: 20px; border-radius: 10px; margin-bottom: 25px; }
        .form-group { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 15px; }
        input, select, button { padding: 10px; border-radius: 6px; border: 1px solid var(--border-color); background: var(--input-bg); color: var(--text-color); }
        input { flex: 1; min-width: 120px; }
        button { background: #00e676; color: #121212; font-weight: bold; cursor: pointer; border: none; }
        button:hover { background: #00c853; }
        .btn-danger { background: #ff5252; color: white; }

        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 12px; border-bottom: 1px solid var(--border-color); text-align: left; }
        th { background: var(--input-bg); color: #00e676; }
        
        .auth-box { max-width: 400px; margin: 80px auto; background: var(--card-bg); border: 1px solid var(--border-color); padding: 30px; border-radius: 12px; }
        .profit { color: #00e676; } .loss { color: #ff5252; }

        /* AI CHATBOX BOX */
        .chat-box { height: 200px; overflow-y: auto; background: var(--input-bg); padding: 10px; border-radius: 8px; margin-bottom: 10px; border: 1px solid var(--border-color); }
        .chat-msg { margin-bottom: 10px; white-space: pre-line; font-size: 14px; }
        .chat-user { color: #29b6f6; font-weight: bold; }
        .chat-ai { color: #00e676; }
    </style>
</head>
<body>
    <div class="container">
        {% if not user %}
        <!-- GİRİŞ / KAYIT EKRANI -->
        <div class="auth-box">
            <h2 style="color:#00e676; text-align:center;">🔐 Finans Portalı Giriş</h2>
            {% if err %}<p style="color:#ff5252; text-align:center;">{{ err }}</p>{% endif %}
            <form method="POST" action="/login">
                <div style="display:flex; flex-direction:column; gap:12px;">
                    <input type="text" name="username" placeholder="Kullanıcı Adı" required>
                    <input type="password" name="password" placeholder="Şifre" required>
                    <button type="submit">Giriş Yap</button>
                    <button type="submit" name="register" value="1" style="background:#29b6f6; color:white;">Kayıt Ol</button>
                </div>
            </form>
        </div>
        {% else %}
        <!-- ANA PANEL -->
        <div class="header-bar">
            <h1>📊 Canlı Finans & Kripto Portalı</h1>
            <div class="nav-btns">
                <span>Hoş geldin, <strong>{{ user }}</strong></span>
                <button onclick="bildirimIzniIste()">🔔 Alarm İzni</button>
                <a href="/logout"><button class="btn-danger">Çıkış Yap</button></a>
            </div>
        </div>

        <!-- CANLI KARTLAR -->
        <div class="cards">
            <div class="card"><h3>💵 Dolar (USD)</h3><div class="price" id="c-USD">₺{{ kurlar['USD'] }}</div></div>
            <div class="card"><h3>💶 Euro (EUR)</h3><div class="price" id="c-EUR">₺{{ kurlar['EUR'] }}</div></div>
            <div class="card"><h3>🪙 Gram Altın</h3><div class="price" id="c-GA">₺{{ kurlar['GA'] }}</div></div>
            <div class="card"><h3>₿ Bitcoin (BTC)</h3><div class="price" id="c-BTC">₺{{ kurlar['BTC'] }}</div></div>
            <div class="card"><h3>Ξ Ethereum (ETH)</h3><div class="price" id="c-ETH">₺{{ kurlar['ETH'] }}</div></div>
        </div>

        <div class="dashboard-grid">
            <!-- PORTFÖY TABLOSU -->
            <div class="section" style="margin-bottom:0;">
                <h2 style="color:#00e676; margin-top:0;">💼 SQLite Veritabanlı Portföyüm</h2>
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
                    <button onclick="dbVarlikEkle()">Veritabanına Ekle</button>
                </div>

                <table>
                    <thead>
                        <tr><th>Varlık</th><th>Miktar</th><th>Alış F.</th><th>Canlı F.</th><th>Mevcut Değer</th><th>K/Z</th><th>İşlem</th></tr>
                    </thead>
                    <tbody id="portfoyBody"></tbody>
                </table>
            </div>

            <!-- CHART.JS GRAFİK ANALİZİ -->
            <div class="section" style="margin-bottom:0;">
                <h2 style="color:#00e676; margin-top:0;">📈 Portföy Dağılım Grafiği</h2>
                <div style="position: relative; height:230px; width:100%;">
                    <canvas id="portfolioChart"></canvas>
                </div>
            </div>
        </div>

        <!-- AKILLI AI ASİSTANI -->
        <div class="section">
            <h2 style="color:#00e676; margin-top:0;">🤖 Akıllı Finansal AI Asistanı</h2>
            <div class="chat-box" id="chatBox">
                <div class="chat-msg chat-ai">🤖 AI: Merhaba! Portföyünüzü ve canlı kurları sizin için analiz edebilirim. Bana "Portföyüm nasıl?" veya "Bana tavsiye ver" yazabilirsiniz!</div>
            </div>
            <div class="form-group" style="margin-bottom:0;">
                <input type="text" id="aiInput" placeholder="AI Asistanına bir soru sorun..." onkeypress="if(event.key==='Enter') aiSoruSor()">
                <button onclick="aiSoruSor()" style="background:#29b6f6; color:white;">Gönder</button>
            </div>
        </div>

        <!-- FİYAT ALARMI EKLENTİSİ -->
        <div class="section">
            <h2 style="color:#00e676; margin-top:0;">🔔 Tarayıcı Fiyat Alarmı Oluştur</h2>
            <div class="form-group">
                <select id="alarmVarlik">
                    <option value="USD">Dolar (USD)</option>
                    <option value="EUR">Euro (EUR)</option>
                    <option value="GA">Gram Altın</option>
                    <option value="BTC">Bitcoin (BTC)</option>
                    <option value="ETH">Ethereum (ETH)</option>
                </select>
                <input type="number" id="alarmHedef" placeholder="Hedef Fiyat (TL)">
                <button onclick="alarmEkle()">Alarmı Kur</button>
            </div>
            <ul id="alarmListesi" style="margin:0; padding-left:20px;"></ul>
        </div>

        <script>
            let KURLAR = {{ kurlar | tojson }};
            let alarmlar = [];
            let myChart = null;

            // Chart.js Başlatma
            function initChart(labels = [], data = []) {
                const ctx = document.getElementById('portfolioChart').getContext('2d');
                if (myChart) myChart.destroy();
                
                myChart = new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: labels,
                        datasets: [{
                            data: data,
                            backgroundColor: ['#00e676', '#29b6f6', '#ffca28', '#ab47bc', '#ff7043'],
                            borderWidth: 1,
                            borderColor: '#1e1e1e'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { labels: { color: '#ffffff' } }
                        }
                    }
                });
            }

            // 10 Saniyede Bir Yenileme
            setInterval(async () => {
                const res = await fetch('/api/kurlar');
                if(res.ok) {
                    KURLAR = await res.json();
                    for(let key in KURLAR) {
                        const el = document.getElementById(`c-${key}`);
                        if(el) el.innerText = `₺${KURLAR[key]}`;
                    }
                    portfoyGetir();
                    alarmKontrol();
                }
            }, 10000);

            function bildirimIzniIste() {
                Notification.requestPermission().then(p => {
                    if(p === 'granted') alert('Fiyat alarmı bildirimleri aktif edildi!');
                });
            }

            function alarmEkle() {
                const varlik = document.getElementById('alarmVarlik').value;
                const hedef = parseFloat(document.getElementById('alarmHedef').value);
                if(!hedef) return;

                alarmlar.push({ varlik, hedef, tetiklendi: false });
                document.getElementById('alarmHedef').value = '';
                alarmListele();
            }

            function alarmListele() {
                const ul = document.getElementById('alarmListesi');
                ul.innerHTML = alarmlar.map(a => `<li><strong>${a.varlik}</strong> için Hedef: ₺${a.hedef}</li>`).join('');
            }

            function alarmKontrol() {
                alarmlar.forEach(a => {
                    if(!a.tetiklendi && KURLAR[a.varlik] >= a.hedef) {
                        a.tetiklendi = true;
                        if(Notification.permission === 'granted') {
                            new Notification('🚨 FİYAT ALARMI TETİKLENDİ!', {
                                body: `${a.varlik} hedef fiyatı geçti! Canlı: ₺${KURLAR[a.varlik]}`
                            });
                        } else {
                            alert(`🚨 ALARM: ${a.varlik} hedef fiyatı geçti! Canlı: ₺${KURLAR[a.varlik]}`);
                        }
                    }
                });
            }

            async function portfoyGetir() {
                const res = await fetch('/api/portfolio');
                const data = await res.json();
                const tbody = document.getElementById('portfoyBody');
                tbody.innerHTML = '';

                let chartLabels = [];
                let chartData = [];

                data.forEach(item => {
                    const canlı = KURLAR[item.code] || 0;
                    const maliyet = item.amount * item.buy_price;
                    const mevcut = item.amount * canlı;
                    const kz = mevcut - maliyet;

                    chartLabels.push(item.code);
                    chartData.push(mevcut.toFixed(2));

                    tbody.innerHTML += `
                        <tr>
                            <td><strong>${item.code}</strong></td>
                            <td>${item.amount}</td>
                            <td>₺${item.buy_price}</td>
                            <td>₺${canlı}</td>
                            <td>₺${mevcut.toFixed(2)}</td>
                            <td class="${kz >= 0 ? 'profit':'loss'}">₺${kz.toFixed(2)}</td>
                            <td><button class="btn-danger" onclick="dbVarlikSil(${item.id})">Sil</button></td>
                        </tr>
                    `;
                });

                initChart(chartLabels, chartData);
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

            async function dbVarlikSil(id) {
                await fetch(`/api/portfolio/delete/${id}`, { method: 'DELETE' });
                portfoyGetir();
            }

            // AI CHAT FONKSİYONU
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

            portfoyGetir();
        </script>
        {% endif %}
    </div>
</body>
</html>
"""

# --- FLASK ROUTE'LARI ---
@app.route('/')
def index():
    user = session.get('user')
    kurlar = kurlari_al()
    return render_template_string(HTML_TEMPLATE, user=user, kurlar=kurlar)

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
            return render_template_string(HTML_TEMPLATE, err="Bu kullanıcı adı zaten alınmış!")
    else:
        cursor.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if row and check_password_hash(row[1], password):
            session['user'] = username
            session['user_id'] = row[0]
        else:
            conn.close()
            return render_template_string(HTML_TEMPLATE, err="Hatalı kullanıcı adı veya şifre!")

    conn.close()
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- REST API (PORTFÖY & KURLAR & AI) ---
@app.route('/api/kurlar')
def api_kurlar():
    return jsonify(kurlari_al())

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
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/api/portfolio/delete/<int:item_id>', methods=['DELETE'])
def delete_portfolio(item_id):
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM portfolio WHERE id = ? AND user_id = ?", (item_id, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    if 'user_id' not in session: return jsonify({'response': 'Lütfen önce giriş yapın.'})
    data = request.json
    prompt = data.get('prompt', '')
    response_text = ai_analiz_ureti(prompt, session['user_id'])
    return jsonify({'response': response_text})

if __name__ == '__main__':
    app.run(debug=True)