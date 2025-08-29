# backend app.py example
# /web_app/backend/app.py
from flask import Flask, jsonify
from flask_cors import CORS
from services.sources import load_sources, SourceConfigError
from services.checker import check_all

app = Flask(__name__)
CORS(app)  # habilita CORS para el frontend

@app.get("/status")
def status():
    """Devuelve el estado de disponibilidad de cada dataset definido en sources.yaml"""
    try:
        datasets = load_sources()
    except SourceConfigError as e:
        return jsonify({"error": str(e)}), 500
    results = check_all(datasets)
    return jsonify({"count": len(results), "results": results})

@app.get("/health")
def health():
    return {"ok": True}

if __name__ == "__main__":
    # Ejecución local: FLASK_APP=app.py flask run --port 5001
    app.run(host="0.0.0.0", port=5001, debug=True)