from flask import Flask, render_template_string, request, jsonify
import requests

app = Flask(__name__)

def kurlari_al():
    usd_try = 34.20
    eur_try = 37.50
    gram_altin = 3050.0  # Varsayılan gerçekçi piyasa yedeği

    # 1. CANLI DÖVİZ VERİSİ (ExchangeRate-API)
    try:
        doviz_res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=4)
        if doviz_res.status_code == 200:
            doviz_data = doviz_res.json()
            usd_try = doviz_data['rates'].get('TRY', usd_try)
            eur_rate = doviz_data['rates'].get('EUR', 1)
            eur_try = usd_try / eur_rate if eur_rate else eur_try
    except Exception as e:
        print("Döviz API Hatası:", e)

    # 2. TÜRKİYE GERÇEK KAPALIÇARŞI / SERBEST PİYASA GRAM ALTIN (Döviz.com Canlı Servisi)
    altin_basarili = False
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        gold_res = requests.get("https://www.doviz.com/api/v1/golds/gram-altin/archive", headers=headers, timeout=4)
        if gold_res.status_code == 200:
            gold_data = gold_res.json()
            if isinstance(gold_data, list) and len(gold_data) > 0:
                # Son güncel gerçek satış fiyatı
                gram_altin = float(gold_data[-1]['selling'])
                altin_basarili = True
    except Exception as e:
        print("Döviz.com Altın API Hatası:", e)

    # Yedek Altın Servisi (Binance Ons -> TL Çevirici + %2 Serbest Piyasa Makası)
    if not altin_basarili:
        try:
            binance_res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT", timeout=4)
            if binance_res.status_code == 200:
                ons_usdt = float(binance_res.json()['price'])
                gram_usd = ons_usdt / 31.1034768
                # Kapalıçarşı primini ekler (~%2.2)
                gram_altin = (gram_usd * usd_try) * 1.022
        except Exception as e:
            print("Yedek Binance Altın Hatası:", e)

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
    <meta name="google-site-verification" content="kwQtL9CdecHzkRTkJOpAPH-Y1vkUs88M-CFZUu6fnXo" />
    
    <title>Canlı Döviz, Gerçek Altın Kurları ve Portföy Takip Portalı</title>
    <meta name="description" content="Canlı Dolar, Euro ve Gerçek Kapalıçarşı Gram Altın fiyatlarını takip edin. Ücretsiz portföy takip aracı ve yapay zeka finans asistanı ile yatırımlarınızı yönetin.">
    <meta name="keywords" content="canlı döviz, kapalıçarşı gram altın, canlı altın, dolar kaç tl, gram altın fiyatı, portföy takip, finans asistanı, kar zarar hesaplama">
    <meta name="author" content="Finans Portalı">
    <meta name="robots" content="index, follow">

    <meta property="og:title" content="Canlı Döviz, Altın & Portföy Takip Portalı">
    <meta property="og:description" content="Canlı piyasa verileri, kişisel portföy hesaplama ve yapay zeka finans asistanı ile yatırımlarınızı anlık takip edin.">
    <meta property="og:type" content="website">

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg-color: #121212;
            --card-bg: #1e1e1e;
            --text-color: #ffffff;
            --subtext-color: #a0a0a0;
            --border-color: #333333;
            --input-bg: #2a2a2a;
            --table-hover: #252525;
            --modal-bg: #1e1e1e;
        }

        body.light-theme {
            --bg-color: #f4f6f8;
            --card-bg: #ffffff;
            --text-color: #1a1a1a;
            --subtext-color: #666666;
            --border-color: #e0e0e0;
            --input-bg: #f0f2f5;
            --table-hover: #f8f9fa;
            --modal-bg: #ffffff;
        }

        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: var(--bg-color); color: var(--text-color); margin: 0; padding: 20px; transition: background 0.3s, color 0.3s; }
        .container { max-width: 1000px; margin: 0 auto; padding-bottom: 80px; }
        
        .header-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        h1 { color: #00e676; margin: 0; font-size: 26px; }
        
        .theme-toggle-btn {
            background: var(--card-bg); color: var(--text-color); border: 1px solid var(--border-color);
            padding: 8px 14px; border-radius: 20px; cursor: pointer; font-size: 16px;
            display: flex; align-items: center; gap: 6px; font-weight: bold; transition: 0.2s;
        }
        .theme-toggle-btn:hover { opacity: 0.8; }

        .cards { display: flex; gap: 20px; justify-content: space-between; margin-bottom: 30px; flex-wrap: wrap; }
        .card { background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 12px; padding: 20px; flex: 1; min-width: 200px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); text-align: center; }
        .card h3 { margin: 0; color: var(--subtext-color); }
        .card .price { font-size: 28px; font-weight: bold; margin: 10px 0; color: #00e676; }
        .card .badge { font-size: 11px; background: #00e67622; color: #00e676; padding: 3px 8px; border-radius: 10px; }
        
        .chart-section, .portfolio-section, .converter-section { background: var(--card-bg); border: 1px solid var(--border-color); padding: 25px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); margin-bottom: 30px; }
        .chart-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 10px; }
        .chart-header h2, .portfolio-section h2, .converter-section h2 { margin: 0; color: #00e676; }
        .chart-btn { background: var(--input-bg); color: var(--subtext-color); border: 1px solid var(--border-color); padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: bold; }
        .chart-btn.active { background: #00e676; color: #121212; border-color: #00e676; }

        .form-group { display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap; }
        input, select, button { padding: 12px; border-radius: 8px; border: 1px solid var(--border-color); background: var(--input-bg); color: var(--text-color); font-size: 16px; }
        input { flex: 1; min-width: 140px; }
        button { background: #00e676; color: #121212; font-weight: bold; cursor: pointer; border: none; transition: 0.2s; }
        button:hover { background: #00c853; }
        .btn-secondary { background: var(--input-bg); color: var(--text-color); border: 1px solid var(--border-color); }
        .btn-secondary:hover { background: var(--border-color); }
        .btn-delete { background: #ff5252; color: white; padding: 6px 12px; font-size: 14px; border-radius: 6px; }

        table { width: 100%; border-collapse: collapse; margin-top: 15px; text-align: left; }
        th, td { padding: 14px; border-bottom: 1px solid var(--border-color); }
        th { background-color: var(--input-bg); color: #00e676; }
        tr:hover { background-color: var(--table-hover); }

        .summary-cards { display: flex; gap: 15px; margin-top: 25px; flex-wrap: wrap; }
        .summary-card { background: var(--input-bg); border: 1px solid var(--border-color); padding: 18px; border-radius: 10px; flex: 1; min-width: 180px; text-align: center; }
        .summary-card span { display: block; font-size: 14px; color: var(--subtext-color); margin-bottom: 5px; }
        .summary-card strong { font-size: 22px; }

        .profit { color: #00e676; }
        .loss { color: #ff5252; }

        /* DÖNÜŞTÜRÜCÜ */
        .converter-box { display: flex; gap: 15px; align-items: center; flex-wrap: wrap; margin-top: 15px; }
        .converter-result { font-size: 20px; font-weight: bold; color: #00e676; margin-top: 15px; }

        /* FOOTER */
        footer { margin-top: 40px; padding: 20px 0; border-top: 1px solid var(--border-color); text-align: center; font-size: 14px; color: var(--subtext-color); }
        footer a { color: #00e676; text-decoration: none; cursor: pointer; margin: 0 10px; font-weight: 500; }
        footer a:hover { text-decoration: underline; }

        /* MODAL */
        .modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); display: none; justify-content: center; align-items: center; z-index: 3000; padding: 20px; box-sizing: border-box; }
        .modal-content { background: var(--modal-bg); border: 1px solid var(--border-color); border-radius: 12px; max-width: 650px; width: 100%; max-height: 80vh; overflow-y: auto; padding: 25px; box-shadow: 0 8px 30px rgba(0,0,0,0.5); position: relative; }
        .modal-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 15px; margin-bottom: 15px; }
        .modal-header h2 { margin: 0; color: #00e676; font-size: 20px; }
        .close-btn { font-size: 24px; cursor: pointer; color: var(--subtext-color); }

        /* AI CHAT */
        .ai-widget-toggle { position: fixed; bottom: 30px; right: 25px; background: #00e676; color: #121212; border-radius: 50%; width: 60px; height: 60px; font-size: 28px; display: flex; justify-content: center; align-items: center; cursor: pointer; box-shadow: 0 4px 15px rgba(0,230,118,0.4); border: none; z-index: 1000; transition: transform 0.2s; }
        .ai-widget-toggle:hover { transform: scale(1.1); }
        .ai-chat-box { position: fixed; bottom: 100px; right: 25px; width: 350px; height: 450px; background: var(--card-bg); border-radius: 12px; border: 1px solid var(--border-color); box-shadow: 0 8px 25px rgba(0,0,0,0.3); display: none; flex-direction: column; z-index: 1000; overflow: hidden; }
        .ai-chat-header { background: var(--input-bg); padding: 15px; color: #00e676; font-weight: bold; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); }
        .ai-chat-messages { flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
        .chat-msg { max-width: 80%; padding: 10px 14px; border-radius: 10px; font-size: 14px; line-height: 1.4; }
        .chat-msg.user { background: #00e676; color: #121212; align-self: flex-end; border-bottom-right-radius: 2px; }
        .chat-msg.ai { background: var(--input-bg); color: var(--text-color); align-self: flex-start; border-bottom-left-radius: 2px; border: 1px solid var(--border-color); }
        .ai-chat-input { display: flex; border-top: 1px solid var(--border-color); padding: 10px; background: var(--card-bg); }
        .ai-chat-input input { flex: 1; border: 1px solid var(--border-color); background: var(--input-bg); color: var(--text-color); border-radius: 6px; padding: 8px 12px; font-size: 14px; }
        .ai-chat-input button { margin-left: 8px; padding: 8px 14px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-bar">
            <h1>📊 Canlı Finans Portalı & Portföy Takibi</h1>
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
                <h3>🪙 24K Gram Altın <span class="badge">Serbest Piyasa</span></h3>
                <div class="price" id="card-ga">₺{{ kurlar['GA'] }}</div>
            </div>
        </div>

        <div class="chart-section">
            <div class="chart-header">
                <h2>📈 Görsel Finans Analizi</h2>
                <div>
                    <button id="btnKurGrafik" class="chart-btn active" onclick="grafikTuruDegistir('kurlar')">Canlı Fiyatlar</button>
                    <button id="btnPortfoyGrafik" class="chart-btn" onclick="grafikTuruDegistir('portfoy')">Portföy Dağılımım</button>
                </div>
            </div>
            <div style="position: relative; height:320px;">
                <canvas id="finansGrafik"></canvas>
            </div>
        </div>

        <!-- DÖNÜŞTÜRÜCÜ / HESAP MAKİNESİ -->
        <div class="converter-section">
            <h2>🧮 Canlı Döviz & Altın Dönüştürücü</h2>
            <div class="converter-box">
                <input type="number" id="convAmount" value="100" oninput="hesaplaDönüstürücü()">
                <select id="convFrom" onchange="hesaplaDönüstürücü()">
                    <option value="USD">Dolar (USD)</option>
                    <option value="EUR">Euro (EUR)</option>
                    <option value="GA">Gram Altın</option>
                    <option value="TRY">Türk Lirası (TL)</option>
                </select>
                <span>➡️</span>
                <select id="convTo" onchange="hesaplaDönüstürücü()">
                    <option value="TRY">Türk Lirası (TL)</option>
                    <option value="USD">Dolar (USD)</option>
                    <option value="EUR">Euro (EUR)</option>
                    <option value="GA">Gram Altın</option>
                </select>
            </div>
            <div class="converter-result" id="convResult">= 0.00 TL</div>
        </div>

        <div class="portfolio-section">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px; flex-wrap:wrap; gap:10px;">
                <h2>💼 Portföy Yönetimi</h2>
                <div>
                    <button class="btn-secondary" onclick="exportPortfoy()">📥 Portföyü İndir</button>
                    <button class="btn-secondary" onclick="document.getElementById('importFile').click()">📤 Yedek Yükle</button>
                    <input type="file" id="importFile" style="display:none" onchange="importPortfoy(event)">
                </div>
            </div>

            <div class="form-group">
                <select id="varlikSecimi">
                    <option value="USD">Dolar (USD)</option>
                    <option value="EUR">Euro (EUR)</option>
                    <option value="GA">24 Ayar Gram Altın</option>
                </select>
                <input type="number" id="varlikMiktar" placeholder="Miktar (Örn: 10)" step="any">
                <input type="number" id="varlikAlis" placeholder="Alış Fiyatı TL (Örn: 3050)" step="any">
                <button onclick="varlikEkle()">Portföye Ekle</button>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Varlık</th>
                        <th>Miktar</th>
                        <th>Ort. Alış</th>
                        <th>Canlı Fiyat</th>
                        <th>Mevcut Değer</th>
                        <th>Kar / Zarar</th>
                        <th>İşlem</th>
                    </tr>
                </thead>
                <tbody id="portfoyTablosu"></tbody>
            </table>

            <div class="summary-cards">
                <div class="summary-card">
                    <span>Toplam Yatırım</span>
                    <strong id="toplamMaliyet">₺0.00</strong>
                </div>
                <div class="summary-card">
                    <span>Mevcut Portföy Değeri</span>
                    <strong id="toplamMevcut">₺0.00</strong>
                </div>
                <div class="summary-card">
                    <span>Toplam Kar / Zarar</span>
                    <strong id="toplamKarZarar">₺0.00</strong>
                </div>
            </div>
        </div>

        <footer>
            <p>© 2026 Canlı Finans Portalı. Tüm hakları saklıdır.</p>
            <p>
                <a onclick="openModal('privacyModal')">Gizlilik Politikası</a> | 
                <a onclick="openModal('termsModal')">Kullanım Şartları</a>
            </p>
        </footer>
    </div>

    <!-- MODALLAR -->
    <div class="modal-overlay" id="privacyModal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>🔒 Gizlilik Politikası</h2>
                <span class="close-btn" onclick="closeModal('privacyModal')">&times;</span>
            </div>
            <div class="modal-body">
                <p>Portföy verileriniz sunucularımızda saklanmaz, sadece kendi tarayıcınızın yerel depolamasında (localStorage) tutulur.</p>
            </div>
        </div>
    </div>

    <div class="modal-overlay" id="termsModal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>📜 Kullanım Şartları</h2>
                <span class="close-btn" onclick="closeModal('termsModal')">&times;</span>
            </div>
            <div class="modal-body">
                <p>Sitemizdeki kurlar bilgilendirme amaçlıdır. Yatırım tavsiyesi (YTD) içermez.</p>
            </div>
        </div>
    </div>

    <!-- AI BOT -->
    <button class="ai-widget-toggle" onclick="toggleAIChat()">🤖</button>
    <div class="ai-chat-box" id="aiChatBox">
        <div class="ai-chat-header">
            <span>🤖 Finans Asistanı AI</span>
            <span style="cursor:pointer;" onclick="toggleAIChat()">✖</span>
        </div>
        <div class="ai-chat-messages" id="aiMessages">
            <div class="chat-msg ai">Merhaba! Portföyün veya canlı kurlar hakkında bana dilediğini sorabilirsin!</div>
        </div>
        <div class="ai-chat-input">
            <input type="text" id="aiInput" placeholder="Bir soru sor..." onkeypress="if(event.key==='Enter') aiSoruSor()">
            <button onclick="aiSoruSor()">Gönder</button>
        </div>
    </div>

    <script>
        let CANLI_KURLAR = {
            'USD': {{ kurlar['USD'] }},
            'EUR': {{ kurlar['EUR'] }},
            'GA': {{ kurlar['GA'] }},
            'TRY': 1.0
        };

        const VARLIK_ISIMLERI = {
            'USD': 'Dolar (USD)',
            'EUR': 'Euro (EUR)',
            'GA': '24 Ayar Gram Altın',
            'TRY': 'Türk Lirası (TL)'
        };

        let portfoy = JSON.parse(localStorage.getItem('portfoy_verileri')) || [];
        let mevcutGrafik = null;
        let aktifGrafikTuru = 'kurlar';

        // OTOMATİK ARKA PLAN YENİLEME (AJAX - 10 saniyede bir)
        setInterval(async () => {
            try {
                const res = await fetch('/api/kurlar');
                if(res.ok) {
                    const yeniKurlar = await res.json();
                    CANLI_KURLAR.USD = yeniKurlar.USD;
                    CANLI_KURLAR.EUR = yeniKurlar.EUR;
                    CANLI_KURLAR.GA = yeniKurlar.GA;

                    document.getElementById('card-usd').innerText = `₺${yeniKurlar.USD}`;
                    document.getElementById('card-eur').innerText = `₺${yeniKurlar.EUR}`;
                    document.getElementById('card-ga').innerText = `₺${yeniKurlar.GA}`;

                    tabloyuGuncelle();
                    hesaplaDönüstürücü();
                }
            } catch(e) { console.error("Kurlar güncellenemedi:", e); }
        }, 10000);

        // TEMA YÖNETİMİ
        if (localStorage.getItem('site_temasi') === 'light') {
            document.body.classList.add('light-theme');
            document.getElementById('themeBtn').innerText = '🌙 Koyu Mod';
        }

        function temaDegistir() {
            document.body.classList.toggle('light-theme');
            const isLight = document.body.classList.contains('light-theme');
            document.getElementById('themeBtn').innerText = isLight ? '🌙 Koyu Mod' : '☀️ Açık Mod';
            localStorage.setItem('site_temasi', isLight ? 'light' : 'dark');
            grafatCiz();
        }

        // HESAP MAKİNESİ / DÖNÜŞTÜRÜCÜ
        function hesaplaDönüstürücü() {
            const amount = parseFloat(document.getElementById('convAmount').value) || 0;
            const from = document.getElementById('convFrom').value;
            const to = document.getElementById('convTo').value;

            const fromTLRate = CANLI_KURLAR[from];
            const toTLRate = CANLI_KURLAR[to];

            const result = (amount * fromTLRate) / toTLRate;
            document.getElementById('convResult').innerText = `= ${result.toFixed(2)} ${to}`;
        }

        // GRAFİK
        function grafatCiz() {
            const ctx = document.getElementById('finansGrafik').getContext('2d');
            if (mevcutGrafik) { mevcutGrafik.destroy(); }

            const isLight = document.body.classList.contains('light-theme');
            const textColor = isLight ? '#1a1a1a' : '#ffffff';

            if (aktifGrafikTuru === 'kurlar') {
                mevcutGrafik = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: ['Dolar (USD)', 'Euro (EUR)', '24K Gram Altın'],
                        datasets: [{
                            label: 'Canlı Fiyat (TL)',
                            data: [CANLI_KURLAR['USD'], CANLI_KURLAR['EUR'], CANLI_KURLAR['GA']],
                            backgroundColor: ['#00e676', '#29b6f6', '#ffd700'],
                            borderRadius: 8
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: {
                            y: { ticks: { color: textColor } },
                            x: { ticks: { color: textColor } }
                        }
                    }
                });
            } else {
                let usdDeger = 0, eurDeger = 0, gaDeger = 0;
                portfoy.forEach(item => {
                    const val = item.miktar * (CANLI_KURLAR[item.kod] || 0);
                    if(item.kod === 'USD') usdDeger += val;
                    if(item.kod === 'EUR') eurDeger += val;
                    if(item.kod === 'GA') gaDeger += val;
                });

                mevcutGrafik = new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: ['Dolar Değeri', 'Euro Değeri', 'Altın Değeri'],
                        datasets: [{
                            data: [usdDeger, eurDeger, gaDeger],
                            backgroundColor: ['#00e676', '#29b6f6', '#ffd700']
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { labels: { color: textColor } } }
                    }
                });
            }
        }

        function grafikTuruDegistir(tur) {
            aktifGrafikTuru = tur;
            document.getElementById('btnKurGrafik').classList.toggle('active', tur === 'kurlar');
            document.getElementById('btnPortfoyGrafik').classList.toggle('active', tur === 'portfoy');
            grafatCiz();
        }

        // TABLO KONTROLÜ
        function tabloyuGuncelle() {
            const tbody = document.getElementById('portfoyTablosu');
            tbody.innerHTML = '';
            let gMaliyet = 0, gMevcut = 0;

            if (portfoy.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:#888;">Henüz eklenmiş bir varlık yok.</td></tr>';
            } else {
                portfoy.forEach((item, index) => {
                    const canlıFiyat = CANLI_KURLAR[item.kod] || 0;
                    const toplamMaliyet = item.miktar * item.alisFiyati;
                    const mevcutDeger = item.miktar * canlıFiyat;
                    const karZarar = mevcutDeger - toplamMaliyet;
                    const karZararYuzde = toplamMaliyet > 0 ? (karZarar / toplamMaliyet) * 100 : 0;

                    gMaliyet += toplamMaliyet;
                    gMevcut += mevcutDeger;

                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td><strong>${VARLIK_ISIMLERI[item.kod]}</strong></td>
                        <td>${item.miktar}</td>
                        <td>₺${item.alisFiyati.toFixed(2)}</td>
                        <td>₺${canlıFiyat.toFixed(2)}</td>
                        <td>₺${mevcutDeger.toFixed(2)}</td>
                        <td class="${karZarar >= 0 ? 'profit' : 'loss'}">${karZarar >= 0 ? '+' : ''}₺${karZarar.toFixed(2)} (%${karZararYuzde.toFixed(2)})</td>
                        <td><button class="btn-delete" onclick="varlikSil(${index})">Sil</button></td>
                    `;
                    tbody.appendChild(tr);
                });
            }

            const genelKarZarar = gMevcut - gMaliyet;
            const genelYuzde = gMaliyet > 0 ? (genelKarZarar / gMaliyet) * 100 : 0;
            document.getElementById('toplamMaliyet').innerText = `₺${gMaliyet.toFixed(2)}`;
            document.getElementById('toplamMevcut').innerText = `₺${gMevcut.toFixed(2)}`;
            const kzElement = document.getElementById('toplamKarZarar');
            kzElement.innerText = `${genelKarZarar >= 0 ? '+' : ''}₺${genelKarZarar.toFixed(2)} (%${genelYuzde.toFixed(2)})`;
            kzElement.className = genelKarZarar >= 0 ? 'profit' : 'loss';

            localStorage.setItem('portfoy_verileri', JSON.stringify(portfoy));
            grafatCiz();
        }

        function varlikEkle() {
            const kod = document.getElementById('varlikSecimi').value;
            const miktar = parseFloat(document.getElementById('varlikMiktar').value);
            const alisFiyati = parseFloat(document.getElementById('varlikAlis').value);

            if (!miktar || !alisFiyati || miktar <= 0 || alisFiyati <= 0) {
                alert('Lütfen geçerli miktar ve alış fiyatı girin!');
                return;
            }

            portfoy.push({ kod, miktar, alisFiyati });
            document.getElementById('varlikMiktar').value = '';
            document.getElementById('varlikAlis').value = '';
            tabloyuGuncelle();
        }

        function varlikSil(index) {
            portfoy.splice(index, 1);
            tabloyuGuncelle();
        }

        // PORTFÖY EXPORT & IMPORT
        function exportPortfoy() {
            const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(portfoy));
            const dlAnchorElem = document.createElement('a');
            dlAnchorElem.setAttribute("href", dataStr);
            dlAnchorElem.setAttribute("download", "portfoy_yedek.json");
            dlAnchorElem.click();
        }

        function importPortfoy(event) {
            const reader = new FileReader();
            reader.onload = function(e) {
                try {
                    portfoy = JSON.parse(e.target.result);
                    tabloyuGuncelle();
                    alert("Portföy başarıyla içe aktarıldı!");
                } catch(err) { alert("Geçersiz yedek dosyası!"); }
            };
            reader.readAsText(event.target.files[0]);
        }

        // AI BOT
        function toggleAIChat() {
            const chatBox = document.getElementById('aiChatBox');
            chatBox.style.display = (chatBox.style.display === 'flex') ? 'none' : 'flex';
        }

        async function aiSoruSor() {
            const input = document.getElementById('aiInput');
            const soru = input.value.trim();
            if(!soru) return;

            const messagesBox = document.getElementById('aiMessages');
            messagesBox.innerHTML += `<div class="chat-msg user">${soru}</div>`;
            input.value = '';
            messagesBox.scrollTop = messagesBox.scrollHeight;

            fetch('/ai_soru', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ soru, portfoy, kurlar: CANLI_KURLAR })
            })
            .then(res => res.json())
            .then(data => {
                messagesBox.innerHTML += `<div class="chat-msg ai">${data.cevap}</div>`;
                messagesBox.scrollTop = messagesBox.scrollHeight;
            });
        }

        function openModal(id) { document.getElementById(id).style.display = 'flex'; }
        function closeModal(id) { document.getElementById(id).style.display = 'none'; }

        // İlk Yükleme
        tabloyuGuncelle();
        hesaplaDönüstürücü();
    </script>
</body>
</html>
"""

@app.route('/')
def ana_sayfa():
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

    if any(k in soru for k in ['portföy', 'portfoy', 'durum']):
        if not portfoy:
            cevap = "Şu anda portföyünüzde kayıtlı hiçbir varlık bulunmuyor."
        else:
            toplam_maliyet = sum(item['miktar'] * item['alisFiyati'] for item in portfoy)
            toplam_mevcut = sum(item['miktar'] * (kurlar.get(item['kod'], 0)) for item in portfoy)
            kar_zarar = toplam_mevcut - toplam_maliyet
            cevap = f"Portföy Toplam Maliyeti: ₺{toplam_maliyet:.2f} | Güncel Değeri: ₺{toplam_mevcut:.2f} | Kâr/Zarar: ₺{kar_zarar:+.2f}"

    elif 'dolar' in soru or 'usd' in soru:
        cevap = f"Canlı Dolar kuru şu anda ₺{kurlar.get('USD', 0)} seviyesinde."
    elif 'euro' in soru or 'eur' in soru:
        cevap = f"Canlı Euro kuru şu anda ₺{kurlar.get('EUR', 0)} seviyesinde."
    elif 'altın' in soru or 'altin' in soru or 'gram' in soru:
        cevap = f"Canlı Serbest Piyasa 24 Ayar Gram Altın fiyatı şu anda ₺{kurlar.get('GA', 0)} seviyesinde."
    else:
        cevap = f"Anlık Kurlar: USD: ₺{kurlar.get('USD')} | EUR: ₺{kurlar.get('EUR')} | Altın: ₺{kurlar.get('GA')}. Bana portföy durumunuzu veya kurları sorabilirsiniz!"

    return jsonify({'cevap': cevap})

if __name__ == '__main__':
    app.run(debug=True)