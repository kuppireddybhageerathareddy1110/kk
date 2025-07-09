import os
from flask import Flask, render_template, request, redirect
from pymongo import MongoClient
from bson import ObjectId
from textblob import TextBlob

app = Flask(__name__, template_folder='../templates', static_folder='../static')

# MongoDB connection
mongo_uri = os.environ.get("MONGODB_URI")
client = MongoClient(mongo_uri)
db = client['sentiment_db']
collection = db['sentiments']

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        text = request.form['text']
        if not text.strip():
            return render_template('index.html', error="Please enter valid text.")

        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        sentiment = 'Positive' if polarity > 0 else 'Negative' if polarity < 0 else 'Neutral'

        collection.insert_one({'text': text, 'sentiment': sentiment, 'polarity': polarity})
        return redirect('/results')

    return render_template('index.html')

@app.route('/results')
def results():
    sentiments = list(collection.find())
    for s in sentiments:
        s['emoji'] = {'Positive': '😊', 'Negative': '😞', 'Neutral': '😐'}.get(s['sentiment'], '')
    
    counts = {
        'Positive': sum(1 for s in sentiments if s['sentiment'] == 'Positive'),
        'Negative': sum(1 for s in sentiments if s['sentiment'] == 'Negative'),
        'Neutral': sum(1 for s in sentiments if s['sentiment'] == 'Neutral'),
    }

    return render_template('results.html', sentiments=sentiments, sentiment_counts=counts)

@app.route('/delete/<id>', methods=['POST'])
def delete(id):
    collection.delete_one({'_id': ObjectId(id)})
    return redirect('/results')

@app.route('/clear', methods=['POST'])
def clear():
    collection.delete_many({})
    return redirect('/results')

# Vercel handler
def handler(environ, start_response):
    return app(environ, start_response)
