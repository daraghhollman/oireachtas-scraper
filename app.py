'''
Script that runs a website locally using a web framework
'''

from flask import Flask, render_template
from flask import g
import sqlite3

app = Flask(__name__)

path = r"dail-debates.db"
def get_database():
    database = getattr(g, '_database', None)
    if database is None:
        database = g._database = sqlite3.connect(path)
        database.row_factory = sqlite3.Row
    return database

@app.teardown_appcontext
def close_connection(exception):
    database = getattr(g, '_database', None)
    if database is not None:
        database.close()

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/dail34")
def dail34():
    return render_template("dail34.html")

@app.route("/dail34/overallstats")
def overallstats34():
    stats = get_database().execute("select words, freq, prob from full_text").fetchall()
    return render_template("overallstat.html", full_text = stats)

@app.route("/dail34/debateindex")
def debateindex34():
    debates = get_database().execute("select id, title, date, category from debates").fetchall()
    return render_template("debateindex.html", debates = debates)

@app.route("/dail34/debateindex/debate/<int:debate_id>")
def debate34(debate_id):
    debate = get_database().execute("select title, id, date from debates where id = ?", (debate_id,)).fetchone()
    prob_dist = get_database().execute(f'select words, freq, prob from "{debate_id}"').fetchall()
    return render_template("debate.html", debate=debate, prob_dist=prob_dist)

@app.route("/dail34/debateindex/debate/<int:debate_id>/text")
def debate34text(debate_id):
    debate = get_database().execute("select title, id, date, text from debates where id = ?", (debate_id,)).fetchone()
    return render_template("debatetext.html", debate=debate)


@app.route("/dail34/tdindex")
def tdindex34():
    return render_template("tdindex.html")

@app.route("/info")
def info():
    return render_template("info.html")

@app.route("/dail33")
def dail33():
    return render_template("dail33.html")
    


if __name__ == '__main__':
    app.run(debug=True)