from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from graphviz import Digraph
import spacy
import os

app = Flask(__name__)
CORS(app)

try:
    nlp = spacy.load("en_core_web_lg")
except OSError:
    print("Downloading en_core_web_lg model...")
    spacy.cli.download("en_core_web_lg")
    nlp = spacy.load("en_core_web_lg")


def generate_dependency_tree(text):
    doc = nlp(text)
    data = []

    # Collect token data and handle det relations
    token_groups = {}  # Store groups of tokens for det relations
    for token in doc:
        data.append({"Index": token.i, "Token": token.text, "POS": token.pos_, "Dependency": token.dep_, "Head": token.head.text, "Head Index": token.head.i})

        if token.dep_ in ["det", "compound","aux"]:
            head_index = token.head.i
            if head_index not in token_groups:
                token_groups[head_index] = []
            token_groups[head_index].append(token.i)

    # Sort the det items by index
    for key, value in token_groups.items():
        token_groups[key] = sorted(value)

    dot = Digraph(comment="Dependency Parse Tree")
    dot.attr('node', shape='box')

    # Add nodes (combine det-related tokens)
    node_labels = {}
    for entry in data:
        index = entry["Index"]
        token = entry["Token"]

        if index in token_groups:
            if index not in node_labels:
                node_labels[index] = ""
            for det_index in token_groups[index]:
                det_token_entry = next((e for e in data if e["Index"] == det_index), None)
                if det_token_entry:
                    node_labels[index] += det_token_entry['Token'] + " "

            node_labels[index] += token

        elif index not in [item for sublist in token_groups.values() for item in sublist]:

            node_labels[index] = token

    # Add nodes to the graph
    for index, label in node_labels.items():
        dot.node(str(index), label=label)

    # Add edges (skip det relations)
    for entry in data:
        index = entry["Index"]
        head_index = entry["Head Index"]
        dependency = entry["Dependency"]
        if index != head_index and entry["Dependency"] != "det" and index not in [item for sublist in token_groups.values() for item in sublist]:
            dot.edge(str(index), str(head_index), label=dependency)

    temp_filename = "dependency_tree_temp"
    dot.render(temp_filename, format="png", cleanup=True)
    return f"{temp_filename}.png"


@app.route('/parse', methods=['POST'])
def parse_sentence():
    try:
        if 'text' not in request.form:
            return jsonify({'error': 'Missing "text" parameter'}), 400

        text = request.form['text']
        image_path = generate_dependency_tree(text)

        if not os.path.exists(image_path):
            return jsonify({'error': 'Failed to generate dependency tree image'}), 500

        return send_file(image_path, mimetype='image/png')

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)