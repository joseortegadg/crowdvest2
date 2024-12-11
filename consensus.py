from flask import Blueprint, send_from_directory, jsonify, request
import requests
import os

# Define the Blueprint, specifying the static folder path
consensus_bp = Blueprint(
    'consensus',
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), '../static'),
)

# Alpha Vantage API key
API_KEY = 'QIFBUAJX9DBVOHRI'

def fetch_sma(symbol, interval='daily', time_period='20'):
    """Fetch SMA data for the given stock symbol."""
    url = (
        f'https://www.alphavantage.co/query?function=SMA'
        f'&symbol={symbol}'
        f'&interval={interval}'
        f'&time_period={time_period}'
        f'&series_type=close'
        f'&apikey={API_KEY}'
    )
    response = requests.get(url)
    data = response.json()
    if 'Technical Analysis: SMA' not in data:
        return None
    sma_data = data['Technical Analysis: SMA']
    latest_date = list(sma_data.keys())[0]
    sma_value = float(sma_data[latest_date]['SMA'])
    return sma_value

def fetch_rsi(symbol, interval='daily', time_period='14'):
    """Fetch RSI data for the given stock symbol."""
    url = (
        f'https://www.alphavantage.co/query?function=RSI'
        f'&symbol={symbol}'
        f'&interval={interval}'
        f'&time_period={time_period}'
        f'&series_type=close'
        f'&apikey={API_KEY}'
    )
    response = requests.get(url)
    data = response.json()
    if 'Technical Analysis: RSI' not in data:
        return None
    rsi_data = data['Technical Analysis: RSI']
    latest_date = list(rsi_data.keys())[0]
    rsi_value = float(rsi_data[latest_date]['RSI'])
    return rsi_value

@consensus_bp.route("/")
def serve_frontend():
    """
    Serve the index.html file as the front end for the consensus API.
    """
    return send_from_directory(consensus_bp.static_folder, 'index.html')

@consensus_bp.route('/market/technical/consensus', methods=['GET'])
def get_consensus():
    """
    Get a consensus recommendation (Buy, Sell, Hold) based on SMA and RSI.
    """
    symbol = request.args.get('symbol')
    interval = request.args.get('interval', 'daily')
    sma_time_period = request.args.get('sma_time_period', '20')
    rsi_time_period = request.args.get('rsi_time_period', '14')

    try:
        sma_value = fetch_sma(symbol, interval, sma_time_period)
        rsi_value = fetch_rsi(symbol, interval, rsi_time_period)

        if sma_value is None or rsi_value is None:
            return jsonify({"msg": "Error retrieving SMA or RSI data"}), 500

        # Example consensus logic
        if rsi_value < 30 and sma_value:  # Oversold
            consensus = "Buy"
        elif rsi_value > 70 and sma_value:  # Overbought
            consensus = "Sell"
        else:
            consensus = "Hold"

        return jsonify({
            "symbol": symbol,
            "interval": interval,
            "sma": sma_value,
            "rsi": rsi_value,
            "consensus": consensus
        }), 200

    except Exception as e:
        return jsonify({"msg": f"Error processing request: {e}"}), 500

