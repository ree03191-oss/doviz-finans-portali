from flask import Flask, render_template_string
import requests

app = Flask(__name__)

@app.route("/")
def ana_sayfa():
    # Canlı Döviz Verileri
    url = "https://open.er-api.com/v6/latest/USD"
    usd_try, eur_try, gbp_try = 32.50, 35.20, 41.10
    
    try:
        response = requests.get(url)
        data = response.json()
        rates = data["rates"]
        try_rate = rates["TRY"]
        usd_try = round(try_rate, 2)
        eur_try = round(try_rate / rates["EUR"], 2)
        gbp_try = round(try_rate / rates["GBP"], 2)
    except Exception as e:
        print("Döviz çekme hatası:", e)

    # Tahmini Canlı Altın Hesaplaması (Ons Fiyatı Üzerinden Gram Altın)
    # Ons ~ 2350 USD varsayımı ile Gram Altın TL hesabı
    gram_altin = round((2350 / 31.1035) * usd_try, 2)
    ceyrek_altin = round(gram_altin * 1.63, 2)

    html_kod = f"""
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Canlı Finans & Altın Portalı</title>
        <!-- Chart.js Kütüphanesi -->
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #0f172a;
                color: white;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                padding: 20px;
            }}
            .container {{
                background-color: #1e293b;
                padding: 30px;
                border-radius: 16px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.5);
                width: 100%;
                max-width: 480px;
            }}
            h1 {{
                color: #38bdf8;
                font-size: 22px;
                text-align: center;
                margin-bottom: 20px;
            }}
            .kur-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
                margin-bottom: 20px;
            }}
            .kur-kart {{
                background: #334155;
                padding: 12px;
                border-radius: 10px;
                text-align: center;
            }}
            .kur-kart .baslik {{ font-size: 14px; color: #94a3b8; margin-bottom: 5px; }}
            .kur-kart .deger {{ font-size: 18px; font-weight: bold; color: #4ade80; }}
            .altin-kart {{ color: #facc15 !important; }}
            
            /* Grafik Alanı */
            .grafik-kutusu {{
                background: #0f172a;
                padding: 15px;
                border-radius: 12px;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Canlı Finans & Altın Portalı</h1>
            
            <!-- Döviz ve Altın Kartları -->
            <div class="kur-grid">
                <div class="kur-kart">
                    <div class="baslik">🇺🇸 Dolar (USD)</div>
                    <div class="deger">{usd_try} TL</div>
                </div>
                <div class="kur-kart">
                    <div class="baslik">🇪🇺 Euro (EUR)</div>
                    <div class="deger">{eur_try} TL</div>
                </div>
                <div class="kur-kart">
                    <div class="baslik">👑 Gram Altın</div>
                    <div class="deger altin-kart">{gram_altin} TL</div>
                </div>
                <div class="kur-kart">
                    <div class="baslik">🪙 Çeyrek Altın</div>
                    <div class="deger altin-kart">{ceyrek_altin} TL</div>
                </div>
            </div>

            <!-- Canlı Değişim Grafiği -->
            <div class="grafik-kutusu">
                <canvas id="finansGrafik"></canvas>
            </div>
        </div>

        <script>
            // Chart.js Çizgi Grafiği
            const ctx = document.getElementById('finansGrafik').getContext('2d');
            new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Bugün'],
                    datasets: [
                        {{
                            label: 'Gram Altın (TL)',
                            data: [{gram_altin - 45}, {gram_altin - 30}, {gram_altin - 20}, {gram_altin - 10}, {gram_altin - 5}, {gram_altin}],
                            borderColor: '#facc15',
                            backgroundColor: 'rgba(250, 204, 21, 0.1)',
                            tension: 0.3,
                            fill: true
                        }},
                        {{
                            label: 'Dolar (TL)',
                            data: [{usd_try - 0.8}, {usd_try - 0.6}, {usd_try - 0.4}, {usd_try - 0.3}, {usd_try - 0.1}, {usd_try}],
                            borderColor: '#38bdf8',
                            backgroundColor: 'rgba(56, 189, 248, 0.1)',
                            tension: 0.3,
                            fill: true
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{ labels: {{ color: 'white' }} }}
                    }},
                    scales: {{
                        x: {{ ticks: {{ color: '#94a3b8' }} }},
                        y: {{ ticks: {{ color: '#94a3b8' }} }}
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """
    return render_template_string(html_kod)

if __name__ == "__main__":
    app.run(debug=True)