from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import os
import pyotp
import time
import logging

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'super-secret-key-2fa')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directory for storing data files
DATA_DIR = os.path.join(os.getcwd(), "data")
DEFAULT_PASSWORD_FILE = os.path.join(DATA_DIR, "default_password.txt")
ID_AUTO_CREATE_FILE = os.path.join(DATA_DIR, "Id_Auto_Creat.txt")
KEY_FILE = os.path.join(DATA_DIR, "2fa_key.txt")

# Ensure data directory exists with proper permissions
try:
    os.makedirs(DATA_DIR, exist_ok=True)
    os.chmod(DATA_DIR, 0o755)
except Exception as e:
    logger.error(f"Failed to create data directory: {str(e)}")

def get_default_password():
    """Read the default password from file."""
    try:
        if os.path.exists(DEFAULT_PASSWORD_FILE):
            with open(DEFAULT_PASSWORD_FILE, "r") as f:
                return f.read().strip()
        return None
    except Exception as e:
        logger.error(f"Error reading default password: {str(e)}")
        return None

@app.route('/')
def index():
    """Render the main menu page."""
    return render_template('index.html')

@app.route('/generate', methods=['GET', 'POST'])
def generate():
    """Generate 2FA codes from a secret key."""
    if request.method == 'POST':
        secret_key = request.form.get('secret_key', '').strip().replace(" ", "")
        if not secret_key:
            flash("Secret key cannot be empty!", "error")
            return redirect(url_for('generate'))
        try:
            totp = pyotp.TOTP(secret_key)
            current_code = totp.now()
            remaining = 30 - (int(time.time()) % 30)
            return render_template('generate.html', code=current_code, remaining=remaining, secret_key=secret_key)
        except Exception as e:
            flash(f"Invalid secret key: {str(e)}", "error")
            logger.error(f"Error generating 2FA code: {str(e)}")
            return redirect(url_for('generate'))
    return render_template('generate.html')

@app.route('/get_2fa_code', methods=['POST'])
def get_2fa_code():
    """API endpoint to fetch 2FA code dynamically."""
    secret_key = request.form.get('secret_key', '').strip().replace(" ", "")
    try:
        totp = pyotp.TOTP(secret_key)
        current_code = totp.now()
        remaining = 30 - (int(time.time()) % 30)
        return jsonify({'code': current_code, 'remaining': remaining})
    except Exception as e:
        logger.error(f"Error fetching 2FA code: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/save', methods=['GET', 'POST'])
def save():
    """Save UID, password, and 2FA key."""
    if request.method == 'POST':
        password = get_default_password()
        if not password:
            flash("No default password set! Please set one first.", "error")
            return redirect(url_for('set_password'))
        
        uid = request.form.get('uid', '').strip()
        secret_key = request.form.get('secret_key', '').strip().replace(" ", "")
        
        if not uid or not secret_key:
            flash("UID and secret key cannot be empty!", "error")
            return redirect(url_for('save'))
        
        try:
            totp = pyotp.TOTP(secret_key)
            current_code = totp.now()
            
            with open(ID_AUTO_CREATE_FILE, 'a') as f:
                f.write(f"{uid}|{password}|{secret_key}\n")
                f.flush()
            os.chmod(ID_AUTO_CREATE_FILE, 0o644)
            
            with open(KEY_FILE, "w") as f:
                f.write(secret_key)
                f.flush()
            os.chmod(KEY_FILE, 0o644)
            
            flash("Data saved successfully!", "success")
            remaining = 30 - (int(time.time()) % 30)
            return render_template('save.html', code=current_code, remaining=remaining, uid=uid, secret_key=secret_key)
        except Exception as e:
            flash(f"Error saving data: {str(e)}", "error")
            logger.error(f"Error saving data: {str(e)}")
            return redirect(url_for('save'))
    return render_template('save.html')

@app.route('/set_password', methods=['GET', 'POST'])
def set_password():
    """Set or update the default password."""
    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        if not password:
            flash("Password cannot be empty!", "error")
            return redirect(url_for('set_password'))
        
        if get_default_password():
            change = request.form.get('change', 'n').strip().lower()
            if change != 'y':
                flash("Password change cancelled.", "info")
                return redirect(url_for('index'))
        
        try:
            with open(DEFAULT_PASSWORD_FILE, "w") as f:
                f.write(password)
                f.flush()
            os.chmod(DEFAULT_PASSWORD_FILE, 0o644)
            flash("Default password saved successfully!", "success")
            return redirect(url_for('index'))
        except Exception as e:
            flash(f"Error saving password: {str(e)}", "error")
            logger.error(f"Error saving password: {str(e)}")
            return redirect(url_for('set_password'))
    
    default_password = get_default_password()
    return render_template('set_password.html', default_password=default_password)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)
else:
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
    