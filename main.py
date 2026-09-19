from flask import Flask, render_template_string, request, jsonify
import requests

app = Flask(__name__)

def kurlari_al():
    usd_try = 34.20
    eur_try = 37.50
    gram_24k_altin = 6870.0

    # 1. Canlı Döviz Kurlarını Çek
    try:
        doviz_res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5)
        if doviz_res.status_code == 200:
            doviz_data = doviz_res.json()
            usd_try = doviz_data['rates']['TRY']
            eur_usd = doviz_data['rates']['EUR']
            eur_try = usd_try / eur_usd
    except Exception as e:
        print("Döviz API Hatası:", e)

    # 2. Canlı 24 Ayar Gram Altın Kuru Çek
    try:
        altin_res = requests.get("https://finans.truncgil.com/v3/today.json", timeout=5)
        if altin_res.status_code == 200:
            altin_data = altin_res.json()
            if 'Gram Altın' in altin_data:
                gram_24k_altin = float(altin_data['Gram Altın']['Selling'].replace(',', '.'))
    except Exception as e:
        print("Altın API Hatası:", e)

    return {
        'USD': round(usd_try, 2),
        'EUR': round(eur_try, 2),
        'GA': round(gram_24k_altin, 2)
    }

HTML_KODU = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <!-- TEMEL SEO ETIKETLERI (Google için) -->
    <meta name="google-site-verification" content="kwQtL9CdecHzkRTkJ0pAPM-YlvkUs88M-CFZUu6fnXo" />
    <title>Canlı Döviz, Altın Kurları ve Portföy Takip Portalı</title>
    <meta name="description" content="Canlı Dolar, Euro ve 24 Ayar Gram Altın fiyatlarını takip edin. Ücretsiz portföy takip aracı ve yapay zeka finans asistanı ile yatırımlarınızı yönetin.">
    <meta name="keywords" content="canlı döviz, canlı altın, dolar kaç tl, gram altın fiyatı, portföy takip, finans asistanı, kar zarar hesaplama">
    <meta name="author" content="Finans Portalı">
    <meta name="robots" content="index, follow">

    <!-- SOSYAL MEDYA PAYLAŞIM KARTLARI (Open Graph & Twitter) -->
    <meta property="og:title" content="Canlı Döviz, Altın & Portföy Takip Portalı">
    <meta property="og:description" content="Canlı piyasa verileri, kişisel portföy hesaplama ve yapay zeka finans asistanı ile yatırımlarınızı anlık takip edin.">
    <meta property="og:type" content="website">
    <meta property="og:image" content="https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1200">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="Canlı Döviz & Portföy Takip Portalı">
    <meta name="twitter:description" content="Canlı döviz, altın kurları ve AI Finans Asistanı ile yatırımlarınızı kolayca yönetin.">

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #121212; color: #ffffff; margin: 0; padding: 20px; }
        .container { max-width: 1000px; margin: 0 auto; padding-bottom: 80px; }
        h1 { text-align: center; color: #00e676; margin-bottom: 30px; }
        .cards { display: flex; gap: 20px; justify-content: space-between; margin-bottom: 30px; flex-wrap: wrap; }
        .card { background: #1e1e1e; border-radius: 12px; padding: 20px; flex: 1; min-width: 200px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); text-align: center; }
        .card h3 { margin: 0; color: #a0a0a0; }
        .card .price { font-size: 28px; font-weight: bold; margin: 10px 0; color: #00e676; }
        
        .chart-section, .portfolio-section { background: #1e1e1e; padding: 25px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); margin-bottom: 30px; }
        .chart-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 10px; }
        .chart-header h2, .portfolio-section h2 { margin: 0; color: #00e676; }
        .chart-btn { background: #2a2a2a; color: #aaa; border: 1px solid #444; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: bold; }
        .chart-btn.active { background: #00e676; color: #121212; border-color: #00e676; }

        .form-group { display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap; }
        input, select, button { padding: 12px; border-radius: 8px; border: 1px solid #333; background: #2a2a2a; color: white; font-size: 16px; }
        input { flex: 1; min-width: 140px; }
        button { background: #00e676; color: #121212; font-weight: bold; cursor: pointer; border: none; transition: 0.2s; }
        button:hover { background: #00c853; }
        .btn-delete { background: #ff5252; color: white; padding: 6px 12px; font-size: 14px; border-radius: 6px; }

        table { width: 100%; border-collapse: collapse; margin-top: 15px; text-align: left; }
        th, td { padding: 14px; border-bottom: 1px solid #333; }
        th { background-color: #2a2a2a; color: #00e676; }
        tr:hover { background-color: #252525; }

        .summary-cards { display: flex; gap: 15px; margin-top: 25px; flex-wrap: wrap; }
        .summary-card { background: #2a2a2a; padding: 18px; border-radius: 10px; flex: 1; min-width: 180px; text-align: center; }
        .summary-card span { display: block; font-size: 14px; color: #aaa; margin-bottom: 5px; }
        .summary-card strong { font-size: 22px; }

        .profit { color: #00e676; }
        .loss { color: #ff5252; }

        /* YAZILIM / AI CHATBOT STİLLERİ */
        .ai-widget-toggle {
            position: fixed; bottom: 25px; right: 25px;
            background: #00e676; color: #121212; border-radius: 50%;
            width: 60px; height: 60px; font-size: 28px;
            display: flex; justify-content: center; align-items: center;
            cursor: pointer; box-shadow: 0 4px 15px rgba(0,230,118,0.4);
            border: none; z-index: 1000; transition: transform 0.2s;
        }
        .ai-widget-toggle:hover { transform: scale(1.1); }

        .ai-chat-box {
            position: fixed; bottom: 95px; right: 25px;
            width: 350px; height: 450px; background: #1e1e1e;
            border-radius: 12px; border: 1px solid #333;
            box-shadow: 0 8px 25px rgba(0,0,0,0.7);
            display: none; flex-direction: column; z-index: 1000;
            overflow: hidden;
        }

        .ai-chat-header {
            background: #2a2a2a; padding: 15px; color: #00e676;
            font-weight: bold; display: flex; justify-content: space-between; align-items: center;
            border-bottom: 1px solid #333;
        }

        .ai-chat-messages {
            flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px;
        }

        .chat-msg { max-width: 80%; padding: 10px 14px; border-radius: 10px; font-size: 14px; line-height: 1.4; }
        .chat-msg.user { background: #00e676; color: #121212; align-self: flex-end; border-bottom-right-radius: 2px; }
        .chat-msg.ai { background: #2a2a2a; color: #ffffff; align-self: flex-start; border-bottom-left-radius: 2px; border: 1px solid #333; }

        .ai-chat-input { display: flex; border-top: 1px solid #333; padding: 10px; background: #181818; }
        .ai-chat-input input { flex: 1; border: none; background: #2a2a2a; color: white; border-radius: 6px; padding: 8px 12px; font-size: 14px; }
        .ai-chat-input button { margin-left: 8px; padding: 8px 14px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Canlı Finans Portalı & Portföy Takibi</h1>
        
        <div class="cards">
            <div class="card">
                <h3>💵 Dolar (USD)</h3>
                <div class="price">₺{{ kurlar['USD'] }}</div>
            </div>
            <div class="card">
                <h3>💶 Euro (EUR)</h3>
                <div class="price">₺{{ kurlar['EUR'] }}</div>
            </div>
            <div class="card">
                <h3>🪙 24 Ayar Gram Altın</h3>
                <div class="price">₺{{ kurlar['GA'] }}</div>
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

        <div class="portfolio-section">
            <h2>💼 Portföy Yönetimi</h2>
            <div class="form-group">
                <select id="varlikSecimi">
                    <option value="USD">Dolar (USD)</option>
                    <option value="EUR">Euro (EUR)</option>
                    <option value="GA">24 Ayar Gram Altın</option>
                </select>
                <input type="number" id="varlikMiktar" placeholder="Miktar (Örn: 10)" step="any">
                <input type="number" id="varlikAlis" placeholder="Alış Fiyatı TL (Örn: 32.5)" step="any">
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
    </div>

    <!-- YAPAY ZEKA SOHBET WIDGET'I -->
    <button class="ai-widget-toggle" onclick="toggleAIChat()">🤖</button>
    <div class="ai-chat-box" id="aiChatBox">
        <div class="ai-chat-header">
            <span>🤖 Finans Asistanı AI</span>
            <span style="cursor:pointer;" onclick="toggleAIChat()">✖</span>
        </div>
        <div class="ai-chat-messages" id="aiMessages">
            <div class="chat-msg ai">Merhaba! Ben Yapay Zeka Finans Asistanın. Kurlar veya portföyün hakkında bana dilediğin soruyu sorabilirsin!</div>
        </div>
        <div class="ai-chat-input">
            <input type="text" id="aiInput" placeholder="Bir soru sor... (Örn: Portföyüm nasıl?)" onkeypress="if(event.key==='Enter') aiSoruSor()">
            <button onclick="aiSoruSor()">Gönder</button>
        </div>
    </div>

    <script>
        const CANLI_KURLAR = {
            'USD': {{ kurlar['USD'] }},
            'EUR': {{ kurlar['EUR'] }},
            'GA': {{ kurlar['GA'] }}
        };

        const VARLIK_ISIMLERI = {
            'USD': 'Dolar (USD)',
            'EUR': 'Euro (EUR)',
            'GA': '24 Ayar Gram Altın'
        };

        let portfoy = JSON.parse(localStorage.getItem('portfoy_verileri')) || [];
        let mevcutGrafik = null;
        let aktifGrafikTuru = 'kurlar';

        function grafatCiz() {
            const ctx = document.getElementById('finansGrafik').getContext('2d');
            if (mevcutGrafik) { mevcutGrafik.destroy(); }

            if (aktifGrafikTuru === 'kurlar') {
                mevcutGrafik = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: ['Dolar (USD)', 'Euro (EUR)', '24K Gram Altın'],
                        datasets: [{
                            label: 'Canlı Piyasa Fiyatı (TL)',
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
                            y: { ticks: { color: '#aaa' }, grid: { color: '#333' } },
                            x: { ticks: { color: '#fff' }, grid: { display: false } }
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
                            backgroundColor: ['#00e676', '#29b6f6', '#ffd700'],
                            borderWidth: 2,
                            borderColor: '#1e1e1e'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { labels: { color: '#ffffff', font: { size: 14 } } } }
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

        /* AI CHATBOT MANTIĞI */
        function toggleAIChat() {
            const chatBox = document.getElementById('aiChatBox');
            chatBox.style.display = (chatBox.style.display === 'flex') ? 'none' : 'flex';
        }

        async function aiSoruSor() {
            const input = document.getElementById('aiInput');
            const soru = input.value.trim();
            if(!soru) return;

            const messagesBox = document.getElementById('aiMessages');
            
            // Kullanıcı Mesajı
            const userMsg = document.createElement('div');
            userMsg.className = 'chat-msg user';
            userMsg.innerText = soru;
            messagesBox.appendChild(userMsg);

            input.value = '';
            messagesBox.scrollTop = messagesBox.scrollHeight;

            // AI Yanıtı
            fetch('/ai_soru', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    soru: soru,
                    portfoy: portfoy,
                    kurlar: CANLI_KURLAR
                })
            })
            .then(res => res.json())
            .then(data => {
                const aiMsg = document.createElement('div');
                aiMsg.className = 'chat-msg ai';
                aiMsg.innerText = data.cevap;
                messagesBox.appendChild(aiMsg);
                messagesBox.scrollTop = messagesBox.scrollHeight;
            });
        }

        tabloyuGuncelle();
    </script>
</body>
</html>
"""

@app.route('/')
def ana_sayfa():
    kurlar = kurlari_al()
    return render_template_string(HTML_KODU, kurlar=kurlar)

@app.route('/ai_soru', methods=['POST'])
def ai_soru():
    data = request.json or {}
    soru = data.get('soru', '').lower()
    portfoy = data.get('portfoy', [])
    kurlar = data.get('kurlar', {})

    if 'portföy' in soru or 'portfoy' in soru or 'durum' in soru:
        if not portfoy:
            cevap = "Şu anda portföyünüzde kayıtlı hiçbir varlık bulunmuyor. Tablodan varlık ekleyerek analizi görebilirsiniz."
        else:
            toplam_maliyet = sum(item['miktar'] * item['alisFiyati'] for item in portfoy)
            toplam_mevcut = sum(item['miktar'] * (kurlar.get(item['kod'], 0)) for item in portfoy)
            kar_zarar = toplam_mevcut - toplam_maliyet
            
            if kar_zarar >= 0:
                cevap = f"Portföyünüz harika durumda! Toplam yatırdığınız {toplam_maliyet:.2f} TL'ye karşılık şu an {toplam_mevcut:.2f} TL değeriniz var. Karınız: +{kar_zarar:.2f} TL."
            else:
                cevap = f"Portföyünüz şu an zararda görünüyor. Toplam yatırdığınız {toplam_maliyet:.2f} TL'ye karşılık değeriniz {toplam_mevcut:.2f} TL. Zararınız: {kar_zarar:.2f} TL."

    elif 'dolar' in soru or 'usd' in soru:
        cevap = f"Canlı Dolar kuru şu anda ₺{kurlar.get('USD', 0)} seviyesinde."
    elif 'euro' in soru or 'eur' in soru:
        cevap = f"Canlı Euro kuru şu anda ₺{kurlar.get('EUR', 0)} seviyesinde."
    elif 'altın' in soru or 'altin' in soru or 'gram' in soru:
        cevap = f"Canlı 24 Ayar Gram Altın fiyatı şu anda ₺{kurlar.get('GA', 0)} seviyesinde."
    elif 'tavsiye' in soru or 'ne yapmalıyım' in soru or 'öneri' in soru:
        cevap = "Finansal yatırımlarınızda riskinizi tek bir varlığa yatırmak yerine Dolar, Euro ve Altın arasında dengeli dağıtmanız önerilir."
    else:
        cevap = f"Anladım. Sorunuz: '{soru}'. Şu anda canlı kurlar: Dolar ₺{kurlar.get('USD')}, Euro ₺{kurlar.get('EUR')}, Gram Altın ₺{kurlar.get('GA')}. Portföyünüz veya kurlar hakkında daha detaylı soru sorabilirsiniz."

    return jsonify({'cevap': cevap})

if __name__ == '__main__':
    app.run(debug=True)