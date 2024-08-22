from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
db = SQLAlchemy(app)

# Define a model for the data
class DataItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now())

# Initialize the database
with app.app_context():
    db.create_all()

def convert_to_timezone(utc_dt, tz_name):
    try:
        target_tz = pytz.timezone(tz_name)
        return utc_dt.astimezone(target_tz)
    except pytz.UnknownTimeZoneError:
        return utc_dt

# Endpoint to fetch data
@app.route('/api/data', methods=['GET'])
def get_data():
    timezone = request.args.get('timezone', 'UTC')  # Default to UTC if no timezone is provided
    items = DataItem.query.order_by(DataItem.timestamp.desc()).all()
    data = [
        {
            "id": item.id,
            "content": item.content,
            "timestamp": convert_to_timezone(item.timestamp, timezone).strftime("You posted this data on %Y-%m-%d at %H:%M:%S %Z")
        } for item in items
    ]
    return jsonify(data)

# Endpoint to post data
@app.route('/api/data', methods=['POST'])
def post_data():
    received_data = request.json.get('content', '')
    new_item = DataItem(content=received_data)
    db.session.add(new_item)
    db.session.commit()
    timezone = request.args.get('timezone', 'PDT')
    converted_timestamp = convert_to_timezone(new_item.timestamp, timezone)
    return jsonify({
        "message": "Data received!",
        "data": {
            "id": new_item.id,
            "content": new_item.content,
            "timestamp": converted_timestamp.strftime("You posted this data on %Y-%m-%d at %H:%M:%S %Z")
        }
    }), 200

# Endpoint to edit data
@app.route('/api/data/<int:data_id>', methods=['PUT'])
def edit_data(data_id):
    item = DataItem.query.get(data_id)
    if not item:
        return jsonify({"message": "Data not found"}), 404

    new_content = request.json.get('content', item.content)
    item.content = new_content
    item.timestamp = datetime.now()  # Update the timestamp to the current time
    db.session.commit()

    timezone = request.args.get('timezone', 'PDT')
    converted_timestamp = convert_to_timezone(item.timestamp, timezone)
    return jsonify({"message": "Data updated!", "data": {
        "id": item.id,
        "content": item.content,
        "timestamp": converted_timestamp.strftime("You updated this data on %Y-%m-%d at %H:%M:%S %Z")
    }})

# Endpoint to Delete data
@app.route('/api/data/<int:data_id>', methods=['DELETE'])
def delete_data(data_id):
    item = DataItem.query.get(data_id)
    if item:
        db.session.delete(item)
        db.session.commit()
        return jsonify({"message": f"Data with ID {data_id} has been deleted!"})
    else:
        return jsonify({"message": f"Data with ID {data_id} not found!"}), 404


if __name__ == '__main__':
    app.run(debug=True)
