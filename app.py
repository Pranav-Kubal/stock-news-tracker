from flask import Flask, render_template, request, redirect
import sqlite3
import requests

app = Flask(__name__)
DB_NAME = "database.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/", methods=["GET", "POST"])
def home():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_name TEXT NOT NULL
        )
    """)

    if request.method == "POST":
        stock = request.form["stock"].upper()
        cursor.execute("INSERT INTO watchlist (stock_name) VALUES (?)", (stock,))
        conn.commit()
        return redirect("/")

    cursor.execute("SELECT * FROM watchlist")
    stocks = cursor.fetchall()
    conn.close()

    return render_template("index.html", stocks=stocks)

NEWS_API_KEY = "YOUR_API_KEY_HERE"

@app.route("/news")
def news():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT stock_name FROM watchlist")
    stocks = [row["stock_name"] for row in cursor.fetchall()]
    conn.close()

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": " OR ".join(stocks),
        "language": "en",
        "sortBy": "publishedAt",
        "apiKey": NEWS_API_KEY
    }


    try:
        response = requests.get(url, params=params)
        data = response.json()
    except Exception as e:
        print("Error fetching news:", e)
        return render_template("news.html", news={})


    filtered_news = {}

    if data.get("status") == "ok":
        for article in data["articles"]:
            title = article["title"] or ""
            description = article["description"] or ""

            for stock in stocks:
                if stock in title.upper() or stock in description.upper():
                    if stock not in filtered_news:
                        filtered_news[stock] = []

                    filtered_news[stock].append({
                        "title": title,
                        "source": article["source"]["name"],
                        "url": article["url"]
                    })

                    break
            
    return render_template("news.html", news=filtered_news)

@app.route("/delete/<int:id>")
def delete_stock(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM watchlist WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
