import os
from flask import Flask, render_template, request, jsonify
import requests
import uuid
#from pgmpy.models import BayesianNetwork
#from pgmpy.factors.discrete import TabularCPD  # Use TabularCPD instead of DiscreteDistribution


app = Flask(__name__)

# Alpha Vantage API key
API_KEY = 'XTT9OCEELPXYT4HA'

# Example list of top 5 most moving stocks (you can change this to be dynamic or based on an external source)
top_stocks = ['AAPL', 'MSFT']

# Function to fetch technical indicators (SMA, RSI, etc.)
def fetch_sma(symbol, interval='daily', time_period='20'):
    url = f'https://www.alphavantage.co/query?function=SMA&symbol={symbol}&interval={interval}&time_period={time_period}&series_type=close&apikey={API_KEY}'
    response = requests.get(url)
    data = response.json()
    if 'Technical Analysis: SMA' not in data:
        return None
    sma_data = data['Technical Analysis: SMA']
    latest_date = list(sma_data.keys())[0]
    return float(sma_data[latest_date]['SMA'])

def fetch_rsi(symbol, interval='daily', time_period='14'):
    url = f'https://www.alphavantage.co/query?function=RSI&symbol={symbol}&interval={interval}&time_period={time_period}&series_type=close&apikey={API_KEY}'
    response = requests.get(url)
    data = response.json()
    if 'Technical Analysis: RSI' not in data:
        return None
    rsi_data = data['Technical Analysis: RSI']
    latest_date = list(rsi_data.keys())[0]
    return float(rsi_data[latest_date]['RSI'])

def fetch_macd(symbol, interval='daily'):
    url = f'https://www.alphavantage.co/query?function=MACD&symbol={symbol}&interval={interval}&apikey={API_KEY}'
    response = requests.get(url)
    data = response.json()
    if 'Technical Analysis: MACD' not in data:
        return None
    macd_data = data['Technical Analysis: MACD']
    latest_date = list(macd_data.keys())[0]
    macd_value = float(macd_data[latest_date]['MACD'])
    return macd_value

def fetch_ema(symbol, interval='daily', time_period='20'):
    url = f'https://www.alphavantage.co/query?function=EMA&symbol={symbol}&interval={interval}&time_period={time_period}&series_type=close&apikey={API_KEY}'
    response = requests.get(url)
    data = response.json()
    if 'Technical Analysis: EMA' not in data:
        return None
    ema_data = data['Technical Analysis: EMA']
    latest_date = list(ema_data.keys())[0]
    return float(ema_data[latest_date]['EMA'])

def fetch_sentiment(symbol):
    url = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&symbol={symbol}&apikey={API_KEY}'
    response = requests.get(url)
    data = response.json()
    
    # Check if 'feed' is in the data and contains articles
    if 'feed' not in data or not data['feed']:
        return None
    
    # Safely extract sentiment scores, ensuring the key exists
    sentiment_scores = []
    for article in data['feed']:
        sentiment_score = article.get('sentiment_score')  # Use .get() to avoid KeyError
        if sentiment_score is not None:
            sentiment_scores.append(sentiment_score)
    
    if sentiment_scores:
        return sum(sentiment_scores) / len(sentiment_scores)
    return None


# Consensus logic based on technical indicators
def get_consensus(sma, rsi, macd, ema):
    consensus = {}
    
    if sma is not None:
        consensus['SMA'] = "Buy" if sma < 50 else "Sell"
    else:
        consensus['SMA'] = "Data not available"
    
    if rsi is not None:
        if rsi < 30:
            consensus['RSI'] = "Buy"
        elif rsi > 70:
            consensus['RSI'] = "Sell"
        else:
            consensus['RSI'] = "Hold"
    else:
        consensus['RSI'] = "Data not available"
    
    if macd is not None:
        consensus['MACD'] = "Buy" if macd > 0 else "Sell"
    else:
        consensus['MACD'] = "Data not available"
    
    if ema is not None:
        consensus['EMA'] = "Buy" if ema < 50 else "Sell"
    else:
        consensus['EMA'] = "Data not available"
    
    return consensus


@app.route('/stock_index')
def stock_index():
    stock_data = []
    
    # Debugging: Print expert forecasts to verify it's populated
    print("Expert Forecasts:", expert_forecasts)
    
    for symbol in top_stocks:
        sma = fetch_sma(symbol)
        rsi = fetch_rsi(symbol)
        macd = fetch_macd(symbol)
        ema = fetch_ema(symbol)
        sentiment_score = fetch_sentiment(symbol)
        
        consensus = get_consensus(sma, rsi, macd, ema)
        
        stock_data.append({
            'symbol': symbol,
            'sma': sma,
            'rsi': rsi,
            'macd': macd,
            'ema': ema,
            'sentiment_score': sentiment_score,
            'consensus': consensus
        })
    
    return render_template('stock_index.html', stock_data=stock_data, expert_forecasts=expert_forecasts)

@app.route('/')
def index():
    return render_template('index.html', top_stocks=top_stocks)


@app.route('/stock/<symbol>')
def stock(symbol):
    sma = fetch_sma(symbol)
    rsi = fetch_rsi(symbol)
    macd = fetch_macd(symbol)
    ema = fetch_ema(symbol)
    sentiment_score = fetch_sentiment(symbol)
    
    consensus = get_consensus(sma, rsi, macd, ema)
    
    stock_data = {
        'symbol': symbol,
        'sma': sma,
        'rsi': rsi,
        'macd': macd,
        'ema': ema,
        'sentiment_score': sentiment_score,
        'consensus': consensus
    }

    return render_template('stock.html', stock_data=stock_data, expert_forecasts=expert_forecasts)


from flask import request, redirect, url_for

# New route to handle expert forecast submissions
@app.route('/forecast/<symbol>', methods=['GET', 'POST'])
def forecast(symbol):
    if request.method == 'POST':
        price_target = request.form['price_target']
        recommendation = request.form['recommendation']
        rationale = request.form['rationale']
        
        # Add the forecast to expert_forecasts
        if symbol not in expert_forecasts:
            expert_forecasts[symbol] = []
        
        expert_forecasts[symbol].append({
            'price_target': price_target,
            'recommendation': recommendation,
            'rationale': rationale
        })

        # Debugging: Print the updated expert forecasts
        print(f"Expert Forecasts for {symbol}: {expert_forecasts[symbol]}")
        
        return redirect(url_for('stock', symbol=symbol))
    
    return render_template('forecast.html', symbol=symbol)

# In-memory storage
applications = {}
reputation_scores = {}

# Routes for rendering HTML
@app.route('/expert')
def expert():
    print("Applications:", applications)
    return render_template('expert.html', applications=applications)

@app.route('/application/', defaults={'application_id': None})
@app.route('/application/<application_id>')
def application_detail(application_id):
    # If no application_id is provided, assign the first available one
    if not application_id:
        if applications:
            application_id = next(iter(applications))  # Get the first key from the applications dictionary
        else:
            return render_template('error.html', message="No applications have been created yet")

    # Retrieve the application data
    app_data = applications.get(application_id)
    if not app_data:
        return render_template('error.html', message="Application not found")
    
    return render_template('application_detail.html', application=app_data)

# API Routes
# API Route: Submit a vote on an expert application
@app.route('/api/experts/vote', methods=['POST'])
def submit_vote():
    data = request.json
    application_id = data.get("application_id")
    vote = data.get("vote")  # 'accept' or 'reject'
    voter_id = data.get("voter_id")
    justification = data.get("justification")

    if application_id not in applications:
        return jsonify({"message": "Application not found"}), 404

    applications[application_id]["votes"].append({
        "voter_id": voter_id,
        "vote": vote,
        "justification": justification
    })
    return jsonify({"message": "Vote submitted"}), 201

# API Route: Calculate consensus score based on votes
@app.route('/api/experts/consensus/<application_id>', methods=['POST'])
def calculate_consensus(application_id):
    if application_id not in applications:
        return jsonify({"message": "Application not found"}), 404

    votes = applications[application_id]["votes"]
    if not votes:
        return jsonify({"message": "No votes available for consensus"}), 400

    # Example Bayesian Network structure for consensus calculation
    expert_vote_dist = DiscreteDistribution({"accept": 0.6, "reject": 0.4})
    crowd_vote_dist = DiscreteDistribution({"accept": 0.5, "reject": 0.5})
    final_consensus = BayesianNetwork.from_structure(
        [(expert_vote_dist, crowd_vote_dist)],
        structure=[[0, 1], [0, 0]]
    )

    consensus_score = final_consensus.probability("accept")
    applications[application_id]["consensus_score"] = consensus_score

    return jsonify({"consensus_score": consensus_score})

# Route to display the application and voting page
# Route to display the application and voting page
@app.route('/vote/', defaults={'application_id': None})
@app.route('/vote/<application_id>')
def vote(application_id):
    if application_id is None:
        # Get the first application ID available
        if applications:
            application_id = next(iter(applications))  # Get the first key from the dictionary
        else:
            return "No applications available to vote on", 404

    if application_id not in applications:
        return "Application not found", 404

    application = applications[application_id]
    consensus_score = application.get("consensus_score", "Not yet calculated")

    return render_template('vote.html', application=application, consensus_score=consensus_score)


# Sample route to apply (used for testing)
@app.route('/api/experts/apply', methods=['POST'])
def submit_application():
    data = request.json
    application_id = str(uuid.uuid4())
    applications[application_id] = {
        "id": application_id,
        "credentials": data.get("credentials"),
        "strategies": data.get("strategies"),
        "performance_history": data.get("performance_history"),
        "votes": [],
        "consensus_score": None
    }
    return jsonify({"message": "Application submitted", "id": application_id}), 201


@app.route('/api/experts/reputation/', defaults={'expert_id': None}, methods=['GET'])
@app.route('/api/experts/reputation/<expert_id>', methods=['GET'])
def get_reputation_score(expert_id):
    # If no expert_id is provided, assign the first available one
    if not expert_id:
        if reputation_scores:
            expert_id = next(iter(reputation_scores))  # Get the first key from the reputation_scores dictionary
        else:
            return jsonify({"message": "No experts have been created yet"}), 404

    # Retrieve feedback for the specified expert
    feedbacks = reputation_scores.get(expert_id, [])
    if not feedbacks:
        return jsonify({"message": f"No feedback found for expert_id: {expert_id}"}), 404

    # Compute reputation score
    reputation = compute_reputation_score(feedbacks)
    return jsonify({"expert_id": expert_id, "reputation_score": reputation}), 200

def compute_reputation_score(feedbacks):
    weighted_scores = [
        f["satisfaction"] * f["credibility"] * f["transaction_size"]
        for f in feedbacks
    ]
    return sum(weighted_scores) / len(feedbacks) if feedbacks else 0

# In-memory storage for expert forecasts (This can be replaced with a database in production)
expert_forecasts = {}

if __name__ == '__main__':
    app.run(debug=True)