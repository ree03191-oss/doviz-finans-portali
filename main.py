from flask import Flask, render_template_string, request
import requests

app = Flask(__name__)

def kurlari_al():
    try:
        # Döviz kurlarını çekiyoruz (Ücretsiz ve hızlı API)
        doviz_res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5)
        doviz_data = doviz_res.json()
        
        usd_try = doviz_data['rates']['TRY']
        eur_usd = doviz_data['rates']['EUR']
        eur_try = usd_try / eur_usd

        # Altın fiyatını Ons üzerinden hesaplıyoruz veya genel kaynak çekiyoruz
        try:
            altin_res = requests.get("https://api.genelpara.com/embed/altin.json", timeout=5)
            altin_data = altin_res.json()
            gram_altin = float(altin_data['GA']['satis'].replace(',', '.'))
        except:
            # AlternatifOns altın hesabı (1 Ons = 31.1035 gram)
            ons_usd = 2650.0  # Yaklaşık Ons
            gram_altin = (ons_usd / 31.1035) * usd_try

        return {
            'USD': round(usd_try, 2),
            'EUR': round(eur_try, 2),
            'GA': round(gram_altin, 2)
        }
    except Exception as e:
        # Bağlantı koparsa bile daha gerçekçi yedek değerler
        return {'USD': 48.70, 'EUR': 52.50, 'GA': 4100.0}

HTML_KODU = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Finans Portalı & Portföy Takibi</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #121212; color: #ffffff; margin: 0; padding: 20px; }
        .container { max-width: 1000px; margin: 0 auto; }
        h1 { text-align: center; color: #00e676; margin-bottom: 30px; }
        .cards { display: flex; gap: 20px; justify-content: space-between; margin-bottom: 30px; flex-wrap: wrap; }
        .card { background: #1e1e1e; border-radius: 12px; padding: 20px; flex: 1; min-width: 200px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); text-align: center; }
        .card h3 { margin: 0; color: #a0a0a0; }
        .card .price { font-size: 28px; font-weight: bold; margin: 10px 0; color: #00e676; }
        .portfolio-section { background: #1e1e1e; padding: 25px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); margin-bottom: 30px; }
        .form-group { display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap; }
        input, select, button { padding: 12px; border-radius: 8px; border: 1px solid #333; background: #2a2a2a; color: white; font-size: 16px; }
        input { flex: 1; min-width: 150px; }
        button { background: #00e676; color: #121212; font-weight: bold; cursor: pointer; border: none; }
        button:hover { background: #00c853; }
        .result-box { background: #2a2a2a; padding: 20px; border-radius: 8px; margin-top: 20px; font-size: 18px; }
        .profit { color: #00e676; font-weight: bold; }
        .loss { color: #ff5252; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Canlı Finans Portalı & Portföy Takibi</h1>
        
        <!-- Canlı Kurlar -->
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
                <h3>🪙 Gram Altın</h3>
                <div class="price">₺{{ kurlar['GA'] }}</div>
            </div>
        </div>

        <!-- Portföy Hesaplayıcı -->
        <div class="portfolio-section">
            <h2>💼 Portföy Kar / Zarar Hesaplama</h2>
            <form method="POST">
                <div class="form-group">
                    <select name="varlik">
                        <option value="USD">Dolar (USD)</option>
                        <option value="EUR">Euro (EUR)</option>
                        <option value="GA">Gram Altın</option>
                    </select>
                    <input type="number" step="any" name="miktar" placeholder="Miktar (Örn: 100)" required>
                    <input type="number" step="any" name="alis_fiyati" placeholder="Alış Fiyatın (TL)" required>
                    <button type="submit">Hesapla</button>
                </div>
            </form>

            {% if hesaplama %}
            <div class="result-box">
                <p><strong>Seçilen Varlık:</strong> {{ hesaplama.varlik_adi }}</p>
                <p><strong>Miktar:</strong> {{ hesaplama.miktar }}</p>
                <p><strong>Mevcut Canlı Değer:</strong> ₺{{ "%.2f"|format(hesaplama.toplam_mevcut) }}</p>
                <p><strong>Toplam Yatırımın:</strong> ₺{{ "%.2f"|format(hesaplama.toplam_maliyet) }}</p>
                <p><strong>Kar / Zarar Durumu:</strong> 
                    <span class="{{ 'profit' if hesaplama.kar_zarar >= 0 else 'loss' }}">
                        ₺{{ "%.2f"|format(hesaplama.kar_zarar) }} (%{{ "%.2f"|format(hesaplama.yuzde) }})
                    </span>
                </p>
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def ana_sayfa():
    kurlar = kurlari_al()
    hesaplama = None

    if request.method == 'POST':
        varlik = request.form.get('varlik')
        miktar = float(request.form.get('miktar', 0))
        alis_fiyati = float(request.form.get('alis_fiyati', 0))

        guncel_fiyat = kurlar.get(varlik, 0)
        toplam_maliyet = miktar * alis_fiyati
        toplam_mevcut = miktar * guncel_fiyat
        kar_zarar = toplam_mevcut - toplam_maliyet
        yuzde = (kar_zarar / toplam_maliyet * 100) if toplam_maliyet > 0 else 0

        varlik_adlari = {'USD': 'Dolar', 'EUR': 'Euro', 'GA': 'Gram Altın'}

        hesaplama = {
            'varlik_adi': varlik_adlari.get(varlik, varlik),
            'miktar': miktar,
            'toplam_maliyet': toplam_maliyet,
            'toplam_mevcut': toplam_mevcut,
            'kar_zarar': kar_zarar,
            'yuzde': yuzde
        }

    return render_template_string(HTML_KODU, kurlar=kurlar, hesaplama=hesaplama)

if __name__ == '__main__':
    app.run(debug=True)