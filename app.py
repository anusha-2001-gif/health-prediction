
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from groq import Groq

# Flask App
app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Groq AI Client
client = Groq(
    api_key="YOUR-API-KEY"
)

# Patient Table
class Patient(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(db.String(100), nullable=False)

    dob = db.Column(db.String(20), nullable=False)

    email = db.Column(db.String(100), nullable=False)

    glucose = db.Column(db.Float, nullable=False)

    haemoglobin = db.Column(db.Float, nullable=False)

    cholesterol = db.Column(db.Float, nullable=False)

    remarks = db.Column(db.String(500))


# Create Database
with app.app_context():
    db.create_all()


# Home Page
@app.route('/')
def index():

    patients = Patient.query.all()

    return render_template('index.html', patients=patients)


# Add Patient
@app.route('/add', methods=['GET', 'POST'])
def add_patient():

    if request.method == 'POST':

        full_name = request.form['full_name']
        dob = request.form['dob']
        email = request.form['email']
        glucose = request.form['glucose']
        haemoglobin = request.form['haemoglobin']
        cholesterol = request.form['cholesterol']

        # Email validation
        if '@' not in email or '.' not in email:
            return "Invalid Email Address"

        # DOB validation
        try:
            dob_date = datetime.strptime(dob, "%Y-%m-%d")

            if dob_date > datetime.today():
                return "Date of Birth Cannot Be Future Date"

        except:
            return "Invalid Date of Birth Format"

        # Numeric validation
        try:
            glucose = float(glucose)
            haemoglobin = float(haemoglobin)
            cholesterol = float(cholesterol)

        except:
            return "Blood Values Must Be Numeric"

        # AI Prediction (Groq)
        try:

            prompt = f"""
            You are a medical assistant.

            Analyze these blood test values:

            Glucose: {glucose}
            Haemoglobin: {haemoglobin}
            Cholesterol: {cholesterol}
            Give a VERY BRIEF health remark in 1–2 lines only.
            Do not explain in detail.
            Just mention possible risk or normal condition.
            Be concise and simple.

            """

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )

            remarks = response.choices[0].message.content

        except:
            remarks = "AI Prediction Failed"

        # Save to database
        patient = Patient(
            full_name=full_name,
            dob=dob,
            email=email,
            glucose=glucose,
            haemoglobin=haemoglobin,
            cholesterol=cholesterol,
            remarks=remarks
        )

        db.session.add(patient)
        db.session.commit()

        return redirect('/')

    return render_template('add.html')


# Edit Patient
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_patient(id):

    patient = Patient.query.get(id)

    if request.method == 'POST':

        patient.full_name = request.form['full_name']
        patient.dob = request.form['dob']
        patient.email = request.form['email']
        patient.glucose = float(request.form['glucose'])
        patient.haemoglobin = float(request.form['haemoglobin'])
        patient.cholesterol = float(request.form['cholesterol'])

        # Recalculate AI Remarks
        try:

            prompt = f"""
            You are a medical assistant.

            Re-analyze updated blood values:

            Glucose: {patient.glucose}
            Haemoglobin: {patient.haemoglobin}
            Cholesterol: {patient.cholesterol}
             Give a VERY BRIEF health remark in 1–2 lines only.
            Do not explain in detail.
            Just mention possible risk or normal condition.
            Be concise and simple.
            """

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )

            patient.remarks = response.choices[0].message.content

        except:
            patient.remarks = "AI Prediction Failed"

        db.session.commit()

        return redirect('/')

    return render_template('edit.html', patient=patient)


# Delete Patient
@app.route('/delete/<int:id>')
def delete_patient(id):

    patient = Patient.query.get(id)

    db.session.delete(patient)
    db.session.commit()

    return redirect('/')


# Run App
if __name__ == '__main__':

    app.run(debug=True)
