from flask import Flask, render_template_string
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
    <title>Canlı Finans Portalı & Portföy Takibi</title>
    <!-- Chart.js Kütüphanesi -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #121212; color: #ffffff; margin: 0; padding: 20px; }
        .container { max-width: 1000px; margin: 0 auto; }
        h1 { text-align: center; color: #00e676; margin-bottom: 30px; }
        .cards { display: flex; gap: 20px; justify-content: space-between; margin-bottom: 30px; flex-wrap: wrap; }
        .card { background: #1e1e1e; border-radius: 12px; padding: 20px; flex: 1; min-width: 200px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); text-align: center; }
        .card h3 { margin: 0; color: #a0a0a0; }
        .card .price { font-size: 28px; font-weight: bold; margin: 10px 0; color: #00e676; }
        
        /* Grafik Bölümü */
        .chart-section { background: #1e1e1e; padding: 25px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); margin-bottom: 30px; }
        .chart-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 10px; }
        .chart-header h2 { margin: 0; color: #00e676; }
        .chart-btn { background: #2a2a2a; color: #aaa; border: 1px solid #444; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: bold; }
        .chart-btn.active { background: #00e676; color: #121212; border-color: #00e676; }

        /* Portföy Bölümü */
        .portfolio-section { background: #1e1e1e; padding: 25px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); margin-bottom: 30px; }
        .form-group { display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap; }
        input, select, button { padding: 12px; border-radius: 8px; border: 1px solid #333; background: #2a2a2a; color: white; font-size: 16px; }
        input { flex: 1; min-width: 140px; }
        button { background: #00e676; color: #121212; font-weight: bold; cursor: pointer; border: none; transition: 0.2s; }
        button:hover { background: #00c853; }
        .btn-delete { background: #ff5252; color: white; padding: 6px 12px; font-size: 14px; border-radius: 6px; }
        .btn-delete:hover { background: #d50000; }

        /* Tablo */
        table { width: 100%; border-collapse: collapse; margin-top: 15px; text-align: left; }
        th, td { padding: 14px; border-bottom: 1px solid #333; }
        th { background-color: #2a2a2a; color: #00e676; }
        tr:hover { background-color: #252525; }

        /* Özet Kutuları */
        .summary-cards { display: flex; gap: 15px; margin-top: 25px; flex-wrap: wrap; }
        .summary-card { background: #2a2a2a; padding: 18px; border-radius: 10px; flex: 1; min-width: 180px; text-align: center; }
        .summary-card span { display: block; font-size: 14px; color: #aaa; margin-bottom: 5px; }
        .summary-card strong { font-size: 22px; }

        .profit { color: #00e676; }
        .loss { color: #ff5252; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Canlı Finans Portalı & Portföy Takibi</h1>
        
        <!-- Canlı Piyasa Kurları -->
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

        <!-- Canlı Grafik Alanı -->
        <div class="chart-section">
            <div class="chart-header">
                <h2>📈 Görsel Finans Analizi</h2>
                <div>
                    <button id="btnKurGrafik" class="chart-btn active" onclick="grafikTuruDegistir('kurlar')">Canlı Fiyatlar</button>
                    <button id="btnPortfoyGrafik" class="chart-btn" onclick="grafikTuruDegistir('portfoy')">Portföy Dağılımım (TL)</button>
                </div>
            </div>
            <div style="position: relative; height:320px;">
                <canvas id="finansGrafik"></canvas>
            </div>
        </div>

        <!-- İnteraktif Portföy Tablosu -->
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

        // Grafik Başlatma
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
                // Portföy Dağılım Grafiği (Pasta Grafiği)
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
                        plugins: {
                            legend: { labels: { color: '#ffffff', font: { size: 14 } } }
                        }
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

            let gMaliyet = 0;
            let gMevcut = 0;

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

                    const classIsmi = karZarar >= 0 ? 'profit' : 'loss';
                    const isaret = karZarar >= 0 ? '+' : '';

                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td><strong>${VARLIK_ISIMLERI[item.kod]}</strong></td>
                        <td>${item.miktar}</td>
                        <td>₺${item.alisFiyati.toFixed(2)}</td>
                        <td>₺${canlıFiyat.toFixed(2)}</td>
                        <td>₺${mevcutDeger.toFixed(2)}</td>
                        <td class="${classIsmi}">${isaret}₺${karZarar.toFixed(2)} (%${karZararYuzde.toFixed(2)})</td>
                        <td><button class="btn-delete" onclick="varlikSil(${index})">Sil</button></td>
                    `;
                    tbody.appendChild(tr);
                });
            }

            const genelKarZarar = gMevcut - gMaliyet;
            const genelYuzde = gMaliyet > 0 ? (genelKarZarar / gMaliyet) * 100 : 0;
            const genelClass = genelKarZarar >= 0 ? 'profit' : 'loss';
            const genelIsaret = genelKarZarar >= 0 ? '+' : '';

            document.getElementById('toplamMaliyet').innerText = `₺${gMaliyet.toFixed(2)}`;
            document.getElementById('toplamMevcut').innerText = `₺${gMevcut.toFixed(2)}`;
            
            const kzElement = document.getElementById('toplamKarZarar');
            kzElement.innerText = `${genelIsaret}₺${genelKarZarar.toFixed(2)} (%${genelYuzde.toFixed(2)})`;
            kzElement.className = genelClass;

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

        tabloyuGuncelle();
    </script>
</body>
</html>
"""

@app.route('/')
def ana_sayfa():
    kurlar = kurlari_al()
    return render_template_string(HTML_KODU, kurlar=kurlar)

if __name__ == '__main__':
    app.run(debug=True)