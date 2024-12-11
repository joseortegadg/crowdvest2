from flask import Flask, request, jsonify, render_template
import uuid
from pgmpy.models import BayesianNetwork
from pgmpy.factors.discrete import TabularCPD  # Use TabularCPD instead of DiscreteDistribution


app = Flask(__name__)

# In-memory storage
applications = {}
reputation_scores = {}

# Routes for rendering HTML
@app.route('/')
def index():
    return render_template('expert.html', applications=applications)

@app.route('/application/<application_id>')
def application_detail(application_id):
    app_data = applications.get(application_id)
    if not app_data:
        return render_template('error.html', message="Application not found")
    return render_template('application_detail.html', application=app_data)

# API Routes
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

@app.route('/api/experts/consensus/<application_id>', methods=['POST'])
def calculate_consensus(application_id):
    if application_id not in applications:
        return jsonify({"message": "Application not found"}), 404

    votes = applications[application_id]["votes"]
    if not votes:
        return jsonify({"message": "No votes available for consensus"}), 400

    # Example Bayesian Network structure
    expert_vote_dist = DiscreteDistribution({"accept": 0.6, "reject": 0.4})
    crowd_vote_dist = DiscreteDistribution({"accept": 0.5, "reject": 0.5})
    final_consensus = BayesianNetwork.from_structure(
        [(expert_vote_dist, crowd_vote_dist)],
        structure=[[0, 1], [0, 0]]
    )

    consensus_score = final_consensus.probability("accept")
    applications[application_id]["consensus_score"] = consensus_score

    return jsonify({"consensus_score": consensus_score})

@app.route('/api/experts/reputation/<expert_id>', methods=['GET'])
def get_reputation_score(expert_id):
    feedbacks = reputation_scores.get(expert_id, [])
    if not feedbacks:
        return jsonify({"message": "No feedback found"}), 404

    reputation = compute_reputation_score(feedbacks)
    return jsonify({"reputation_score": reputation})

def compute_reputation_score(feedbacks):
    weighted_scores = [
        f["satisfaction"] * f["credibility"] * f["transaction_size"]
        for f in feedbacks
    ]
    return sum(weighted_scores) / len(feedbacks) if feedbacks else 0

if __name__ == "__main__":
    app.run(debug=True)

