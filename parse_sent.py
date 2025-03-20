from flask import Flask, request, send_file, jsonify
from flask_cors import CORS  # Import the CORS module
from graphviz import Digraph
import spacy
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes in the app

# 加载英语模型 (只加载一次)
try:
    nlp = spacy.load("en_core_web_lg")
except OSError:
    print("Downloading en_core_web_lg model...")
    spacy.cli.download("en_core_web_lg")
    nlp = spacy.load("en_core_web_lg")


def generate_dependency_tree(text):
    """生成依赖树的PNG图像."""
    doc = nlp(text)
    data = []

    for token in doc:
        data.append({"Index": token.i, "Token": token.text, "POS": token.pos_, "Dependency": token.dep_, "Head": token.head.text, "Head Index": token.head.i})

    dot = Digraph(comment="Dependency Parse Tree")
    dot.attr('node', shape='box')

    for entry in data:
        index = entry["Index"]
        token = entry["Token"]
        dot.node(str(index), label=token)

    for entry in data:
        index = entry["Index"]
        head_index = entry["Head Index"]
        dependency = entry["Dependency"]
        if index != head_index:
            dot.edge(str(index), str(head_index), label=dependency)

    # 使用临时文件名，避免冲突
    temp_filename = "dependency_tree_temp"
    dot.render(temp_filename, format="png", cleanup=True)
    return f"{temp_filename}.png"


@app.route('/parse', methods=['POST'])
def parse_sentence():
    """API端点，接收文本并返回依赖树图像."""
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
    """健康检查接口"""
    return jsonify({'status': 'ok'}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)