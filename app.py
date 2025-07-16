from flask import Flask, request, jsonify
from aws_helpers import get_template, create_changeset
from utils import make_subnet_private

app = Flask(__name__)

@app.route('/template/<stack_name>', methods=['GET'])
def get_cf_template(stack_name):
    try:
        template = get_template(stack_name)
        return jsonify(template), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/template/private', methods=['PUT'])
def update_template():
    try:
        template_json = request.get_json()
        modified_template = make_subnet_private(template_json)
        return jsonify(modified_template), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/changeset', methods=['POST'])
def create_changeset_endpoint():
    data = request.get_json()
    stack_name = data.get("stack_name")
    template_body = data.get("template_body")

    try:
        response = create_changeset(stack_name, template_body)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)