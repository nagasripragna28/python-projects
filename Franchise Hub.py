from flask import Flask, render_template, request, redirect, url_for, session,jsonify
from datetime import datetime
import sqlite3
from flask_mail import Mail, Message
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Used to keep the user logged in

# Initialize Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'franchisehub14@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'dxtd agck ezaj lqxr'   # Replace with your password
app.config['MAIL_DEFAULT_SENDER'] = 'franchisehub14@gmail.com'
mail = Mail(app)

UPLOAD_FOLDER = 'static/uploads/logos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def get_db_connection():
    conn = sqlite3.connect('franchise_hub.db')
    return conn

def init_db():

    conn = get_db_connection()
    cursor = conn.cursor()

    # Create tables with additional columns for email and phone
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            user_type TEXT CHECK(user_type IN ('franchisee', 'franchisor')) NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            details TEXT
        )
    ''')
    # Create the table if it doesn't already exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS franchises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand_name TEXT NOT NULL,
        industry TEXT NOT NULL,
        price INTEGER NOT NULL,
        description TEXT,
        location_availability TEXT,
        franchisor_id INTEGER,
        logo TEXT,  -- Column for storing logo or brand image
        company_page_path TEXT,  -- Column for storing file path or link to the company page
        FOREIGN KEY (franchisor_id) REFERENCES users(id)
    )
''')


    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            franchise_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            details TEXT,  
            purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES users(username),
            FOREIGN KEY (franchise_id) REFERENCES franchises(id)
        )
    ''')
    conn.execute('''
            CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            franchise_id INTEGER NOT NULL,
            applicant_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            contact_no TEXT NOT NULL,
            email TEXT NOT NULL,
            details TEXT NOT NULL,
            submitted_on TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (franchise_id) REFERENCES franchises (id),
            FOREIGN KEY (applicant_id) REFERENCES users (id)
            )
    ''')

    conn.commit()
    cursor.close()
    conn.close()
    print("SQLite database initialized and tables created successfully!")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login_view():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.json  # Expecting JSON input
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    phone = data.get('phone')
    user_type = data.get('user_type')

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (username, password, email, phone, user_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, password, email, phone, user_type))
        conn.commit()
        return jsonify({"status": "success", "message": "User registered successfully"}), 201
    except sqlite3.IntegrityError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/signin', methods=['POST'])
def signin():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT password,id FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        if user and user[0] == password:  # Check if password matches
            session['username'] = username
            session['user_id'] = user[1]
            return jsonify({"status": "success", "message": "Sign-in successful"}), 200
        else:
            return jsonify({"status": "error", "message": "Invalid username or password"}), 401
    finally:
        cursor.close()
        conn.close()

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login_view'))  # Redirect if the user is not logged in
    
    username = session['username']
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Query the user_type of the logged-in user
        cursor.execute('SELECT user_type FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        if user:
            user_type = user[0]
            if user_type == 'franchisor':
                return render_template('franchisor_dashboard.html')  # Render a specific template for franchisors
            else:
                return render_template('franchisee_dashboard.html')  # Render a template for franchisees
        else:
            return redirect(url_for('login_view'))  # Redirect if the user is not found
    finally:
        cursor.close()
        conn.close()

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/api/franchises_all', methods=['GET'])
def get_franchises_all():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM franchises')
    franchises = cursor.fetchall()
    cursor.close()
    conn.close()

    # Convert the list of franchises into a list of dictionaries to return as JSON
    franchise_list = []
    for franchise in franchises:
        franchise_list.append({
            "id": franchise[0],
            "brand_name": franchise[1],
            "industry": franchise[2],
            "price": franchise[3],
            "description": franchise[4],
            "location_availability": franchise[5],
            "logo": franchise[7],  # Include logo file path
            "html_file": franchise[8],  # Include HTML file path
        })

    return jsonify({"status": "success", "franchises": franchise_list}), 200

@app.route('/api/franchises', methods=['GET'])
def get_franchises():
    if 'username' not in session:
        return jsonify({"status": "error", "message": "User not logged in"}), 401

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get franchisor ID based on session username
    cursor.execute('SELECT id FROM users WHERE username = ?', (session['username'],))
    user = cursor.fetchone()
    if not user:
        return jsonify({"status": "error", "message": "Invalid user"}), 401
    
    franchisor_id = user[0]

    # Get franchises for this franchisor
    cursor.execute('SELECT * FROM franchises WHERE franchisor_id = ?', (franchisor_id,))
    franchises = cursor.fetchall()
    
    # Include the new HTML file column in the response
    franchise_list = [
        {
            "id": row[0],
            "brand_name": row[1],
            "industry": row[2],
            "price": row[3],
            "description": row[4],
            "location_availability": row[5],
            "logo": row[7],  # Include the logo column in the response
            "html_file": row[8]  # Include the HTML file column in the response
        } for row in franchises
    ]

    cursor.close()
    conn.close()
    return jsonify({"status": "success", "franchises": franchise_list}), 200

@app.route('/api/applications/<int:franchise_id>', methods=['GET'])
def get_applications(franchise_id):
    if 'username' not in session:
        return jsonify({"status": "error", "message": "User not logged in"}), 401

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify that the logged-in user is the owner of the franchise
    cursor.execute(''' 
        SELECT COUNT(*) FROM franchises
        WHERE id = ? AND franchisor_id = (SELECT id FROM users WHERE username = ?)
    ''', (franchise_id, session['username']))
    ownership = cursor.fetchone()
    if ownership[0] == 0:
        return jsonify({"status": "error", "message": "Unauthorized access"}), 403

    # Get applications for this franchise from the applications table
    cursor.execute('''
        SELECT id, full_name, contact_no, email, details, submitted_on,status
        FROM applications
        WHERE franchise_id = ?
    ''', (franchise_id,))
    applications = cursor.fetchall()

    application_list = [
        {"id": row[0], "full_name": row[1], "contact_no": row[2], 
         "email": row[3], "details": row[4], "submitted_on": row[5], "status": row[6]} for row in applications
    ]

    cursor.close()
    conn.close()
    
    return jsonify({"status": "success", "applications": application_list}), 200

@app.route('/api/applications/<int:application_id>/<action>', methods=['POST'])
def handle_application(application_id, action):
    try:
        # Validate action
        if action not in ['approve', 'reject']:
            return jsonify({"status": "error", "message": "Invalid action."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Retrieve application and related franchise details
        cursor.execute('''
            SELECT a.franchise_id, a.full_name, a.email, a.details, f.brand_name, a.email
            FROM applications a
            JOIN franchises f ON a.franchise_id = f.id
            WHERE a.id = ?
        ''', (application_id,))
        application = cursor.fetchone()

        if not application:
            return jsonify({"status": "error", "message": "Application not found."}), 404

        franchise_id, full_name, applicant_email, details, brand_name, franchise_email = application

        # Handle the application based on the action
        if action == 'approve':
            cursor.execute('''UPDATE applications SET status = 'approved' WHERE id = ?''', (application_id,))
            conn.commit()

            # Send email to the franchise owner
            try:
                msg = Message(
                    subject=f"New Franchise Application Approved: {brand_name}",
                    recipients=[franchise_email],
                    body=(
                        f"Dear Franchise Owner,\n\n"
                        f"The following application for your franchise '{brand_name}' has been approved:\n\n"
                        f"Applicant Name: {full_name}\n"
                        f"Applicant Email: {applicant_email}\n"
                        f"Application Details: {details}\n\n"
                        f"Please reach out to the applicant to proceed further.\n\n"
                        f"Best regards,\nFranchise Hub Team"
                    )
                )
                mail.send(msg)
            except Exception as email_error:
                print(f"Error sending email: {email_error}")
                return jsonify({
                    "status": "error",
                    "message": "Application approved, but failed to send email.",
                    "error": str(email_error)
                }), 500

        elif action == 'reject':
            cursor.execute('''UPDATE applications SET status = 'rejected' WHERE id = ?''', (application_id,))
            conn.commit()

        # Close connection
        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": f"Application {action}d successfully.", "franchise_id": franchise_id})

    except Exception as e:
        print(f"Error handling application {action}: {e}")
        return jsonify({"status": "error", "message": "An error occurred while processing the application."}), 500

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/add-franchise', methods=['POST']) #done
def add_franchise():
    if 'username' not in session:
        return jsonify({"status": "error", "message": "User not logged in"}), 401

    # Check if the logo file is in the request
    if 'logo' not in request.files or 'html_file' not in request.files:
        return jsonify({"status": "error", "message": "Logo or HTML file is missing"}), 400

    logo_file = request.files['logo']
    html_file = request.files['html_file']

    # Check if the files are allowed
    if logo_file.filename == '' or not allowed_file(logo_file.filename):
        return jsonify({"status": "error", "message": "Invalid logo file type"}), 400

    if html_file.filename == '' or not html_file.filename.endswith('.html'):
        return jsonify({"status": "error", "message": "Invalid HTML file type"}), 400

    # Secure the file names and save them
    logo_filename = secure_filename(logo_file.filename)
    html_filename = secure_filename(html_file.filename)
    logo_file_path = os.path.join(app.config['UPLOAD_FOLDER'], logo_filename)
    html_file_path = os.path.join(app.config['UPLOAD_FOLDER'], html_filename)
    logo_file.save(logo_file_path)
    html_file.save(html_file_path)

    # Get other franchise details from the request
    data = request.form  # Use form data since files and text data are sent separately in multipart requests
    brand_name = data.get('brand_name')
    industry = data.get('industry')
    price = data.get('price')
    description = data.get('description')
    location_availability = data.get('location_availability')

    # Validate required fields
    if not all([brand_name, industry, price]):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get franchisor ID
    cursor.execute('SELECT id FROM users WHERE username = ?', (session['username'],))
    user = cursor.fetchone()
    if not user:
        return jsonify({"status": "error", "message": "Invalid user"}), 401

    franchisor_id = user[0]

    # Insert franchise into the database
    cursor.execute('''
        INSERT INTO franchises (brand_name, industry, price, description, location_availability, logo, company_page_path, franchisor_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (brand_name, industry, price, description, location_availability, logo_file_path, html_file_path, franchisor_id))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"status": "success", "message": "Franchise added successfully!"}), 201

@app.route('/api/apply', methods=['POST'])
def apply():
    try:
        # Parse application data from the request
        data = request.json
        franchise_id = data.get('franchise_id')
        applicant_id = session.get('user_id')  # Assuming user_id is stored in the session
        full_name = data.get('full_name')
        contact_no = data.get('contact_no')
        email = data.get('email')
        details = data.get('details')

        # Validate input
        if not all([franchise_id, applicant_id, full_name, contact_no, email, details]):
            return jsonify({"status": "error", "message": "All fields are required."}), 400

        # Insert the application into the database
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(''' 
            INSERT INTO applications (franchise_id, applicant_id, full_name, contact_no, email, details, submitted_on)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (franchise_id, applicant_id, full_name, contact_no, email, details, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()

        return jsonify({"status": "success", "message": "Application submitted successfully."})

    except Exception as e:
        print(f"Error in /api/apply: {e}")
        return jsonify({"status": "error", "message": "An error occurred while submitting the application."}), 500

@app.route('/api/user_applications', methods=['GET'])
def get_user_applications():
    # Get the applicant ID from the session
    applicant_id = session.get('user_id')  # Assuming you store user_id in the session
    if not applicant_id:
        return jsonify({"message": "User not logged in"}), 401

    try:
        conn = get_db_connection()
        query = '''
            SELECT a.id, f.brand_name, a.status, a.submitted_on, a.details
            FROM applications a
            JOIN franchises f ON a.franchise_id = f.id
            WHERE a.applicant_id = ?
        '''
        cursor = conn.execute(query, (applicant_id,))
        applications = cursor.fetchall()
        print(applications)
        if not applications:
            return jsonify([])  # No applications found for the user

        # Prepare the response
        response = [
            {
                'application_id': application['id'],
                'franchise_name': application['brand_name'],
                'status': application['status'],
                'submitted_on': datetime.strptime(application['submitted_on'], '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y'),
                'details': application['details']
            }
            for application in applications
        ]
        conn.close()
        return jsonify(response)

    except Exception as e:
        print(f"Error in /api/user_applications: {e}")
        return jsonify({"status": "error", "message": "An error occurred while fetching user applications."}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
