from flask import Flask, request, jsonify
from parser_service.parser import main as parser_script

app = Flask(__name__)

@app.route('/parse', methods=['POST'])
def parse():
    data = request.json
    category = data.get('category', 'SALE > Shop Deals > Hat Sale')
    
    result = parser_script(category)
    return jsonify({"status": "done", "category": category, "result": result})