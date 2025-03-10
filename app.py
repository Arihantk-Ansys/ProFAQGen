from flask import Flask, render_template, request, jsonify
import json
import time
from modules.text_enrichment import enrich_data, compiler
from modules.generateFAQ import generate_faq_with_llm
from modules.PII import OpenAI_PII_removal
from modules.DiscussionAnalysis import discussion_main, get_report_modes

app = Flask(__name__)

# Function to generate summary and FAQs
def generate_summary_and_faqs(body, physics=None, product=None):
    """
    Generate an FAQ from a given text, where the text consists of a subject, a description, and a discussion.
    Ensure that the body is a single combined string, starting with the subject, followed by the description, and then the sequential interactions or discussions.
    
    Parameters:
    -----------
    body : str
        The combined text containing subject, description, and body content
    physics : str, optional
        The physics/family information if available
    product : str, optional
        The product/application information if available

    Returns:
    --------
    dict
        A dictionary containing the generated summary and FAQs
    """
    
    # Clean the text to remove PII
    clean_text = OpenAI_PII_removal(body)
    
    # Generate a unique case ID for discussion analysis
    case_id = f"temp_{int(time.time())}"
    
    # Analyze the discussion
    report = discussion_main(clean_text, case_id)
    discussion_type, classification = get_report_modes(report)
    
    # Check if data should be processed based on discussion type and classification
    if discussion_type == 1:
        if classification == 'LLM Data Enrichment':
            # Enrich the data using the physics parameter if provided
            enriched_data = enrich_data(clean_text, physics=physics)
        elif classification == 'Good to go for Classification Agent':
            # Use compiler function for this classification
            switch = 'prompt2'
            retrieved_data = ''
            enriched_data = compiler(clean_text, retrieved_data, switch)
        else:
            return {"error": "Discussion discarded"}
    else:
        return {"error": "Discussion is open-ended"}
    
    # Generate FAQ if data was successfully summarized
    no_words = len(enriched_data.split())
    faq_generated = generate_faq_with_llm(enriched_data, no_words)
    
    # Try to parse FAQ response as JSON
    try:
        faq_json = json.loads(faq_generated)
    except json.JSONDecodeError:
        faq_json = {"error": "Failed to generate valid FAQ JSON"}
    
    return {
        "summary": enriched_data,
        "faqs": faq_json
    }

@app.route('/')
def index():
    return render_template('index.html')

# API to process text input and generate summary + FAQs
@app.route('/process', methods=['POST'])
def process_text():
    data = request.json
    user_input = data.get("text", "")
    physics = data.get("physics", None)
    product = data.get("product", None)

    if not user_input.strip():
        return jsonify({"error": "Input text cannot be empty"}), 400

    response_data = generate_summary_and_faqs(user_input, physics, product)
    
    return jsonify(response_data)

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
