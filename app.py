import os
from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# Initialize Flask app and database
app = Flask(__name__, static_folder="frontend", static_url_path="")
app.debug = True
app.secret_key = "secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///hsp.sqlite3"
db = SQLAlchemy(app)
CORS(app)

# Models
class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Data(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())

# API key
API_KEY = "5588"

# Serve React build files
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react_app(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

# API routes
@app.route('/register_device', methods=['GET'])
def register_device():
    api_key = request.args.get('API-Key')
    if api_key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 403

    device_name = request.args.get('device_name')
    if not device_name:
        return jsonify({"error": "Device name is required"}), 400

    new_device = Device(name=device_name)
    db.session.add(new_device)
    db.session.commit()
    return jsonify({"message": "Device registered successfully!", "device_id": new_device.id})

@app.route('/update_data', methods=['GET'])
def update_data():
    api_key = request.args.get('API-Key')
    if api_key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 403

    device_name = request.args.get('device_name')
    temperature = request.args.get('temperature')
    humidity = request.args.get('humidity')

    if not all([device_name, temperature, humidity]):
        return jsonify({"error": "All fields (device_name, temperature, humidity) are required"}), 400

    try:
        temperature = float(temperature)
        humidity = float(humidity)
    except ValueError:
        return jsonify({"error": "Invalid data format"}), 400

    device = Device.query.filter_by(name=device_name).first()
    if not device:
        return jsonify({"error": "Device not found"}), 404

    new_data = Data(device_id=device.id, temperature=temperature, humidity=humidity)
    db.session.add(new_data)
    db.session.commit()
    return jsonify({"message": f"Data updated successfully for device {device.name}!"})

@app.route('/get_data', methods=['GET'])
def get_data():
    device_id = request.args.get('device_id')
    device = Device.query.get(device_id)
    if not device:
        return jsonify({"error": "Device not found"}), 404

    data = Data.query.filter_by(device_id=device_id).all()
    data_list = [{"temperature": d.temperature, "humidity": d.humidity, "timestamp": d.timestamp} for d in data]
    return jsonify({"device_name": device.name, "data": data_list})

if __name__ == "__main__":
    app.run(debug=True)
