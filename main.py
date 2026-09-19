from flask import Flask, render_template_string, request, jsonify
import requests

app = Flask(__name__)

def kurlari_al():
    # Varsayılan (Yedek/Fallback) Fiyatlar
    usd_try = 34.20
    eur_try = 37.50
    gram_altin = 2950.0

    # 1. DÖVİZ VERİSİ ÇEKME (ExchangeRate-API)
    try:
        doviz_res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=3)
        if doviz_res.status_code == 200:
            doviz_data = doviz_res.json()
            usd_try = doviz_data['rates'].get('TRY', usd_try)
            eur_rate = doviz_data['rates'].get('EUR', 1)
            eur_try = usd_try / eur_rate if eur_rate else eur_try
    except Exception as e:
        print("Döviz API Bağlantı Uyarısı:", e)

    # 2. ANLIK GRAM ALTIN HESAPLAMA (Binance Canlı PAXG/USDT & USD/TRY)
    try:
        # PAXG/USDT (Ons Altın) fiyatını Binance'ten al
        gold_res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT", timeout=3)
        if gold_res.status_code == 200:
            ons_usdt = float(gold_res.json()['price'])
            # 1 Ons = ~31.1034768 Gram Has Altın
            gram_usd = ons_usdt / 31.1034768
            gram_altin = gram_usd * usd_try
    except Exception as e:
        print("Altın API Bağlantı Uyarısı:", e)

    return {
        'USD': round(usd_try, 2),
        'EUR': round(eur_try, 2),
        'GA': round(gram_altin, 2)
    }

HTML_KODU = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Canlı Döviz, Altın & Portföy Portalı</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg-color: #121212;
            --card-bg: #1e1e1e;
            --text-color: #ffffff;
            --subtext-color: #a0a0a0;
            --border-color: #333333;
            --input-bg: #2a2a2a;
        }

        body.light-theme {
            --bg-color: #f4f6f8;
            --card-bg: #ffffff;
            --text-color: #1a1a1a;
            --subtext-color: #666666;
            --border-color: #e0e0e0;
            --input-bg: #f0f2f5;
        }

        body { font-family: 'Segoe UI', Tahoma, sans-serif; background-color: var(--bg-color); color: var(--text-color); margin: 0; padding: 20px; transition: 0.3s; }
        .container { max-width: 1000px; margin: 0 auto; }
        
        .header-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        h1 { color: #00e676; margin: 0; font-size: 24px; }
        
        .theme-toggle-btn { background: var(--card-bg); color: var(--text-color); border: 1px solid var(--border-color); padding: 8px 14px; border-radius: 20px; cursor: pointer; font-weight: bold; }

        .cards { display: flex; gap: 15px; margin-bottom: 25px; flex-wrap: wrap; }
        .card { background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 12px; padding: 20px; flex: 1; min-width: 200px; text-align: center; }
        .card h3 { margin: 0; color: var(--subtext-color); font-size: 16px; }
        .card .price { font-size: 26px; font-weight: bold; margin: 10px 0; color: #00e676; }

        .section-box { background: var(--card-bg); border: 1px solid var(--border-color); padding: 20px; border-radius: 12px; margin-bottom: 25px; }
        
        .form-group { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
        input, select, button { padding: 10px; border-radius: 6px; border: 1px solid var(--border-color); background: var(--input-bg); color: var(--text-color); }
        input { flex: 1; min-width: 120px; }
        button { background: #00e676; color: #121212; font-weight: bold; cursor: pointer; border: none; }
        button:hover { background: #00c853; }
        .btn-delete { background: #ff5252; color: white; padding: 5px 10px; border-radius: 4px; }

        table { width: 100%; border-collapse: collapse; text-align: left; }
        th, td { padding: 12px; border-bottom: 1px solid var(--border-color); }
        th { color: #00e676; background: var(--input-bg); }

        .profit { color: #00e676; }
        .loss { color: #ff5252; }

        /* AI WIDGET */
        .ai-toggle { position: fixed; bottom: 25px; right: 25px; background: #00e676; color: #121212; border-radius: 50%; width: 55px; height: 55px; font-size: 26px; display: flex; justify-content: center; align-items: center; cursor: pointer; border: none; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
        .ai-box { position: fixed; bottom: 90px; right: 25px; width: 320px; height: 400px; background: var(--card-bg); border-radius: 12px; border: 1px solid var(--border-color); display: none; flex-direction: column; box-shadow: 0 8px 20px rgba(0,0,0,0.4); }
        .ai-header { background: var(--input-bg); padding: 12px; color: #00e676; font-weight: bold; display: flex; justify-content: space-between; }
        .ai-messages { flex: 1; padding: 12px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; font-size: 14px; }
        .msg-user { background: #00e676; color: #121212; padding: 8px 12px; border-radius: 8px; align-self: flex-end; }
        .msg-ai { background: var(--input-bg); color: var(--text-color); padding: 8px 12px; border-radius: 8px; align-self: flex-start; border: 1px solid var(--border-color); }
        .ai-input { display: flex; padding: 8px; border-top: 1px solid var(--border-color); }
        .ai-input input { flex: 1; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-bar">
            <h1>📊 Canlı Finans Portalı</h1>
            <button class="theme-toggle-btn" onclick="temaDegistir()" id="themeBtn">☀️ Açık Mod</button>
        </div>
        
        <div class="cards">
            <div class="card">
                <h3>💵 Dolar (USD)</h3>
                <div class="price" id="card-usd">₺{{ kurlar['USD'] }}</div>
            </div>
            <div class="card">
                <h3>💶 Euro (EUR)</h3>
                <div class="price" id="card-eur">₺{{ kurlar['EUR'] }}</div>
            </div>
            <div class="card">
                <h3>🪙 Gram Altın</h3>
                <div class="price" id="card-ga">₺{{ kurlar['GA'] }}</div>
            </div>
        </div>

        <div class="section-box">
            <h2 style="color:#00e676; margin-top:0;">📈 Canlı Grafik</h2>
            <div style="position: relative; height:250px;">
                <canvas id="finansGrafik"></canvas>
            </div>
        </div>

        <div class="section-box">
            <h2 style="color:#00e676; margin-top:0;">💼 Portföyüm</h2>
            <div class="form-group">
                <select id="varlikSecimi">
                    <option value="USD">Dolar (USD)</option>
                    <option value="EUR">Euro (EUR)</option>
                    <option value="GA">Gram Altın</option>
                </select>
                <input type="number" id="varlikMiktar" placeholder="Miktar" step="any">
                <input type="number" id="varlikAlis" placeholder="Alış Fiyatı (TL)" step="any">
                <button onclick="varlikEkle()">Ekle</button>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Varlık</th>
                        <th>Miktar</th>
                        <th>Alış</th>
                        <th>Güncel</th>
                        <th>Toplam Değer</th>
                        <th>Kâr/Zarar</th>
                        <th>İşlem</th>
                    </tr>
                </thead>
                <tbody id="portfoyTablosu"></tbody>
            </table>
        </div>
    </div>

    <button class="ai-toggle" onclick="toggleAI()">🤖</button>
    <div class="ai-box" id="aiBox">
        <div class="ai-header">
            <span>🤖 Finans Asistanı</span>
            <span style="cursor:pointer;" onclick="toggleAI()">✖</span>
        </div>
        <div class="ai-messages" id="aiMessages">
            <div class="msg-ai">Selam! Portföyün veya canlı piyasa hakkında bana soru sorabilirsin.</div>
        </div>
        <div class="ai-input">
            <input type="text" id="aiInput" placeholder="Sorunu yaz..." onkeypress="if(event.key==='Enter') aiSor()">
            <button onclick="aiSor()">></button>
        </div>
    </div>

    <script>
        let KURLAR = { 'USD': {{ kurlar['USD'] }}, 'EUR': {{ kurlar['EUR'] }}, 'GA': {{ kurlar['GA'] }} };
        let portfoy = JSON.parse(localStorage.getItem('portfoy_verileri')) || [];
        let grafik = null;

        // TEMA MANTIĞI
        function temaDegistir() {
            document.body.classList.toggle('light-theme');
            const isLight = document.body.classList.contains('light-theme');
            document.getElementById('themeBtn').innerText = isLight ? '🌙 Koyu Mod' : '☀️ Açık Mod';
            grafikCiz();
        }

        // 10 SANİYEDE BİR OTOMATİK VERİ YENİLEME (AJAX)
        setInterval(async () => {
            try {
                const res = await fetch('/api/kurlar');
                if(res.ok) {
                    KURLAR = await res.json();
                    document.getElementById('card-usd').innerText = `₺${KURLAR.USD}`;
                    document.getElementById('card-eur').innerText = `₺${KURLAR.EUR}`;
                    document.getElementById('card-ga').innerText = `₺${KURLAR.GA}`;
                    tabloGuncelle();
                    grafikCiz();
                }
            } catch(e) { console.error("Kurlar güncellenemedi:", e); }
        }, 10000);

        // GRAFİK
        function grafikCiz() {
            const ctx = document.getElementById('finansGrafik').getContext('2d');
            if (grafik) grafik.destroy();
            
            const isLight = document.body.classList.contains('light-theme');
            
            grafik = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Dolar', 'Euro', 'Gram Altın'],
                    datasets: [{
                        label: 'Canlı Fiyat (TL)',
                        data: [KURLAR.USD, KURLAR.EUR, KURLAR.GA],
                        backgroundColor: ['#00e676', '#29b6f6', '#ffd700'],
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { ticks: { color: isLight ? '#1a1a1a' : '#fff' } },
                        x: { ticks: { color: isLight ? '#1a1a1a' : '#fff' } }
                    }
                }
            });
        }

        // PORTFÖY İŞLEMLERİ
        function tabloGuncelle() {
            const tbody = document.getElementById('portfoyTablosu');
            tbody.innerHTML = '';

            portfoy.forEach((item, index) => {
                const guncelFiyat = KURLAR[item.kod] || 0;
                const toplamMaliyet = item.miktar * item.alisFiyati;
                const mevcutDeger = item.miktar * guncelFiyat;
                const karZarar = mevcutDeger - toplamMaliyet;

                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><b>${item.kod}</b></td>
                    <td>${item.miktar}</td>
                    <td>₺${item.alisFiyati.toFixed(2)}</td>
                    <td>₺${guncelFiyat.toFixed(2)}</td>
                    <td>₺${mevcutDeger.toFixed(2)}</td>
                    <td class="${karZarar >= 0 ? 'profit' : 'loss'}">${karZarar >= 0 ? '+' : ''}₺${karZarar.toFixed(2)}</td>
                    <td><button class="btn-delete" onclick="varlikSil(${index})">X</button></td>
                `;
                tbody.appendChild(tr);
            });

            localStorage.setItem('portfoy_verileri', JSON.stringify(portfoy));
        }

        function varlikEkle() {
            const kod = document.getElementById('varlikSecimi').value;
            const miktar = parseFloat(document.getElementById('varlikMiktar').value);
            const alisFiyati = parseFloat(document.getElementById('varlikAlis').value);

            if (miktar > 0 && alisFiyati > 0) {
                portfoy.push({ kod, miktar, alisFiyati });
                document.getElementById('varlikMiktar').value = '';
                document.getElementById('varlikAlis').value = '';
                tabloGuncelle();
            }
        }

        function varlikSil(i) {
            portfoy.splice(i, 1);
            tabloGuncelle();
        }

        // AI CHAT
        function toggleAI() {
            const box = document.getElementById('aiBox');
            box.style.display = box.style.display === 'flex' ? 'none' : 'flex';
        }

        function aiSor() {
            const input = document.getElementById('aiInput');
            const soru = input.value.trim();
            if(!soru) return;

            const msgs = document.getElementById('aiMessages');
            msgs.innerHTML += `<div class="msg-user">${soru}</div>`;
            input.value = '';

            fetch('/ai_soru', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ soru, portfoy, kurlar: KURLAR })
            })
            .then(r => r.json())
            .then(data => {
                msgs.innerHTML += `<div class="msg-ai">${data.cevap}</div>`;
                msgs.scrollTop = msgs.scrollHeight;
            });
        }

        // İlk Yükleme
        tabloGuncelle();
        grafikCiz();
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_KODU, kurlar=kurlari_al())

@app.route('/api/kurlar')
def api_kurlar():
    return jsonify(kurlari_al())

@app.route('/ai_soru', methods=['POST'])
def ai_soru():
    data = request.json or {}
    soru = data.get('soru', '').lower()
    portfoy = data.get('portfoy', [])
    kurlar = data.get('kurlar', {})

    if any(k in soru for k in ['kar', 'karlı', 'kazanç']):
        if not portfoy:
            cevap = "Portföyün boş, önce varlık ekle bakalım!"
        else:
            en_karli = max(portfoy, key=lambda x: (kurlar.get(x['kod'], 0) - x['alisFiyati']) * x['miktar'])
            cevap = f"Şu an en kârlı yatırımların içinde <b>{en_karli['kod']}</b> öne çıkıyor!"
    elif 'dolar' in soru:
        cevap = f"Dolar şu an <b>₺{kurlar.get('USD')}</b> seviyesinde."
    elif 'euro' in soru:
        cevap = f"Euro şu an <b>₺{kurlar.get('EUR')}</b> seviyesinde."
    elif 'altın' in soru or 'altin' in soru:
        cevap = f"Gram Altın şu an <b>₺{kurlar.get('GA')}</b> seviyesinde."
    else:
        cevap = f"Anlık Kurlar: USD: ₺{kurlar.get('USD')} | EUR: ₺{kurlar.get('EUR')} | Altın: ₺{kurlar.get('GA')}. Bana portföy durumunu sorabilirsin!"

    return jsonify({'cevap': cevap})

if __name__ == '__main__':
    app.run(debug=True)