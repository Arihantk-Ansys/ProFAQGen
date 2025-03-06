from flask import Flask, render_template, request, jsonify
import json

app = Flask(__name__)

# Route to render index.html
def generate_summary_and_faqs(text):
    # Placeholder function - Replace with your actual processing logic
    summary = "This is a generated summary of the input text."
    faqs = [
        {"question": "What is this about?", "answer": "This is about the given text."},
        {"question": "How does it work?", "answer": "It processes the text and generates FAQs."}
    ]
    return summary, faqs

@app.route('/')
def index():
    return render_template('index.html')

# API to process text input and generate summary + FAQs
@app.route('/process', methods=['POST'])
def process_text():
    data = request.json
    user_input = data.get("text", "")
    summary, faqs = generate_summary_and_faqs(user_input)
    return jsonify({"summary": summary, "faqs": faqs})

# API to save accepted and user-added FAQs to JSON
@app.route('/save_faqs', methods=['POST'])
def save_faqs():
    data = request.json
    accepted_faqs = data.get("accepted_faqs", [])
    with open("faqs.json", "w") as f:
        json.dump(accepted_faqs, f, indent=4)
    return jsonify({"message": "FAQs saved successfully!"})

if __name__ == '__main__':
    app.run(debug=True)
