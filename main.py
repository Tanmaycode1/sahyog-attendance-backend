from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import os

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('manager.id'), nullable=False)


class Manager(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    checkin_time = db.Column(db.Time, nullable=True)
    checkout_time = db.Column(db.Time, nullable=True)
    working_day_type = db.Column(db.String(50), nullable=True)  # Short leave, Half day, etc.


with app.app_context():
    db.create_all()


# Register user
@app.route('/register', methods=['POST'])
def register_user():
    fullname = request.json.get('fullname')
    manager_id = request.json.get('manager_id')

    if not fullname or not manager_id:
        return jsonify({"error": "Fullname and Manager ID are required"}), 400

    new_user = User(fullname=fullname, manager_id=manager_id)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered", "user_id": new_user.id}), 200


# Get all managers
@app.route('/managers', methods=['GET'])
def get_managers():
    managers = Manager.query.all()
    managers_list = [{"id": manager.id, "fullname": manager.fullname} for manager in managers]
    return jsonify(managers_list), 200


# Add manager
@app.route('/add_manager', methods=['POST'])
def add_manager():
    fullname = request.json.get('fullname')

    if not fullname:
        return jsonify({"error": "Fullname is required"}), 400

    new_manager = Manager(fullname=fullname)
    db.session.add(new_manager)
    db.session.commit()

    return jsonify({"message": "Manager added", "manager_id": new_manager.id}), 200


# Delete manager
@app.route('/delete_manager/<int:manager_id>', methods=['DELETE'])
def delete_manager(manager_id):
    manager = Manager.query.get(manager_id)

    if not manager:
        return jsonify({"error": "Manager not found"}), 404

    db.session.delete(manager)
    db.session.commit()

    return jsonify({"message": "Manager deleted"}), 200


@app.route('/checkin', methods=['POST'])
def checkin():
    user_id = request.json.get('user_id')

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    # Check if the user has already checked in today
    today = date.today()
    existing_attendance = Attendance.query.filter_by(user_id=user_id, date=today).first()

    if existing_attendance:
        return jsonify({"error": "User has already checked in today"}), 400

    # Create a new attendance record
    new_attendance = Attendance(user_id=user_id, checkin_time=datetime.now().time(), date=today)
    db.session.add(new_attendance)
    db.session.commit()

    return jsonify({"message": "Checked in successfully", "attendance_id": new_attendance.id}), 200


@app.route('/checkout', methods=['POST'])
def checkout():
    user_id = request.json.get('user_id')

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    # Find the attendance record for the current day and user
    today = date.today()
    attendance = Attendance.query.filter_by(user_id=user_id, date=today).first()

    if not attendance:
        return jsonify({"error": "No check-in record found for today"}), 404

    if attendance.checkout_time is not None:
        return jsonify({"error": "User has already checked out today"}), 400

    # Update the attendance record with the checkout time
    attendance.checkout_time = datetime.now().time()
    db.session.commit()

    return jsonify({"message": "Checked out successfully"}), 200



@app.route('/checkin_status/<int:user_id>', methods=['GET'])
def checkin_status(user_id):
    today = date.today()
    existing_attendance = Attendance.query.filter_by(user_id=user_id, date=today).first()

    if existing_attendance and existing_attendance.checkin_time:
        return jsonify({"checked_in": True}), 200

    return jsonify({"checked_in": False}), 200


@app.route('/', methods=['GET'])
def home():
    manager_id = request.args.get('manager_id')
    date_filter = request.args.get('date')

    query = Attendance.query.join(User).join(Manager)

    if manager_id:
        query = query.filter(User.manager_id == manager_id)

    if date_filter:
        query = query.filter(Attendance.date == date_filter)

    attendance_records = query.all()
    result = []

    for record in attendance_records:
        user = User.query.get(record.user_id)
        manager = Manager.query.get(user.manager_id)
        result.append({
            "user_fullname": user.fullname,
            "manager_fullname": manager.fullname,
            "date": record.date,
            "checkin_time": record.checkin_time,
            "checkout_time": record.checkout_time,
            "working_day_type": record.working_day_type
        })

    # Fetch all managers for the filter dropdown
    managers = Manager.query.all()

    return render_template('home.html', records=result, managers=managers), 200


@app.route('/manage_managers', methods=['GET', 'POST'])
def manage_managers():
    if request.method == 'POST':
        action = request.form.get('action')
        manager_id = request.form.get('manager_id')
        if action == 'add':
            fullname = request.form.get('fullname')
            if not fullname:
                return redirect(url_for('manage_managers', error="Fullname is required"))
            new_manager = Manager(fullname=fullname)
            db.session.add(new_manager)
            db.session.commit()
        elif action == 'delete':
            manager = Manager.query.get(manager_id)
            if manager:
                db.session.delete(manager)
                db.session.commit()
            else:
                return redirect(url_for('manage_managers', error="Manager not found"))

    managers = Manager.query.all()
    return render_template('manage_managers.html', managers=managers), 200


# Export attendance to Excel (placeholder for real implementation)
@app.route('/attendance/download', methods=['GET'])
def download_attendance():
    return jsonify({"message": "Download attendance functionality coming soon!"}), 200


if __name__ == '__main__':
    app.run(debug=True)
