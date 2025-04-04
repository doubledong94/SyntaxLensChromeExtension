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


def should_merge(node1, node2, dependency):
    """
    判断两个节点是否应该合并。这里只定义 det 关系需要合并。
    """
    if dependency in ['aux', 'auxpass', 'amod', 'advmod', 'acomp', 'compound', 'cc', 'case', 'det', 'mark', 'nummod',
                      'npadvmod', 'poss', 'prt', 'predet','pobj', 'punct']:
        return True
    return False


def merge_nodes(data, node1_index, node2_index):
    """合并两个节点，并更新数据结构。"""
    node1 = next((n for n in data if n["Index"] == node1_index), None)
    node2 = next((n for n in data if n["Index"] == node2_index), None)

    if not node1 or not node2:
        return False  # 节点不存在，合并失败

    # 1. 合并后的节点的label是被合并节点label拼接的，拼接注意按照节点原先的先后顺序拼接
    merged_list = (node1["MergedNodes"] if node1["Merged"] else [node1]) + (node2["MergedNodes"] if node2["Merged"] else [node2])
    merged_list.sort(key=lambda x: x["Index"])
    merged_label = " ".join([node["Token"] for node in merged_list])

    # 2. 合并后的节点与剩余节点的关系是由被合并节点中的head节点决定的
    head_node = None
    if node1["Dependency"] == "ROOT":
        head_node = node1
    elif node2["Dependency"] == "ROOT":
        head_node = node2

    elif node1["Head Index"] == node2["Index"]:
        head_node = node2
    elif node2["Head Index"] == node1["Index"]:
        head_node = node1
    else:
        head_node = node1 if node1["Head Index"] != node1["Index"] else node2

    # 创建新的合并节点
    merged_node = {
        "Index": head_node["Index"],  # 使用root的索引作为合并节点的索引
        "Token": merged_label,
        "POS": "MERGED",  # 可以自定义合并后的POS标签
        "Dependency": head_node["Dependency"],
        "Head": head_node["Head"],
        "Head Index": head_node["Head Index"],
        "Merged": True,
        "MergedNodes": merged_list
    }

    # 删除旧节点
    data.remove(node1)
    data.remove(node2)

    # 更新其他节点的关系
    for node in data:
        if node["Head Index"] == node1["Index"] or node["Head Index"] == node2["Index"]:
            node["Head"] = merged_node["Token"]
            node["Head Index"] = merged_node["Index"]

    data.append(merged_node)
    data.sort(key=lambda x: x["Index"])

    return True


def generate_dependency_tree(text):
    """生成依赖树的PNG图像."""
    doc = nlp(text)
    data = []

    for token in doc:
        print(f"Token: {token.text}, POS: {token.pos_}/{spacy.explain(token.pos_)}, Dependency: {token.dep_}/{spacy.explain(token.dep_)}, Head: {token.head.text}, Head Index: {token.head.i}")
        data.append(
            {
                "Index": token.i,
                "Token": token.text,
                "POS": token.pos_,
                "Dependency": token.dep_,
                "Head": token.head.text,
                "Head Index": token.head.i,
                "Merged": False,
                "MergedNodes": []
            }
        )

    # 3. 合并节点后的树如果仍满足合并节点的要求，要继续合并，直到没有满足合并节点的关系为止
    while True:
        merged = False
        # 查找入度为 0 的节点
        leaf_nodes = [node for node in data if all(node["Index"] != other_node["Head Index"] for other_node in data if other_node["Index"] != node["Index"])]
        for leaf_node in leaf_nodes:
            for other_node in data:
                if leaf_node["Index"] != other_node["Index"]:
                    # 4. 每次合并的节点要包含入度为0节点
                    if leaf_node["Head Index"] == other_node["Index"] or other_node["Head Index"] == leaf_node["Index"]:
                        if should_merge(leaf_node, other_node, leaf_node["Dependency"] if leaf_node["Head Index"] == other_node["Index"] else other_node["Dependency"]):
                            merge_nodes(data, leaf_node["Index"], other_node["Index"])
                            merged = True
                            break
            if merged:
                break

        if not merged:
            break

    dot = Digraph(comment="Dependency Parse Tree")
    dot.attr("node", shape="box")

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


@app.route("/parse", methods=["POST"])
def parse_sentence():
    """API端点，接收文本并返回依赖树图像."""
    try:
        if "text" not in request.form:
            return jsonify({"error": 'Missing "text" parameter'}), 400

        text = request.form["text"]
        image_path = generate_dependency_tree(text)

        if not os.path.exists(image_path):
            return jsonify({"error": "Failed to generate dependency tree image"}), 500

        return send_file(image_path, mimetype="image/png")

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """健康检查接口"""
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)
