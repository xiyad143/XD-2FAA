from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import os
import pyotp
import time
import logging

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'super-secret-key-2fa')

# Set up logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
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
    logger.info("Data directory created or exists: %s", DATA_DIR)
except Exception as e:
    logger.error("Failed to create data directory: %s", str(e))

def get_default_password():
    """Read the default password from file."""
    try:
        if os.path.exists(DEFAULT_PASSWORD_FILE):
            with open(DEFAULT_PASSWORD_FILE, "r") as f:
                password = f.read().strip()
                logger.info("Default password read successfully")
                return password
        logger.info("No default password file found")
        return None
    except Exception as e:
        logger.error("Error reading default password: %s", str(e))
        return None

@app.route('/')
def index():
    """Render the main menu page."""
    logger.info("Rendering index page")
    return render_template('index.html')

@app.route('/generate', methods=['GET', 'POST'])
def generate():
    """Generate 2FA codes from a secret key."""
    logger.info("Accessing /generate route: %s", request.method)
    if request.method == 'POST':
        secret_key = request.form.get('secret_key', '').strip().replace(" ", "")
        if not secret_key:
            flash("Secret key cannot be empty!", "error")
            logger.warning("Secret key empty on /generate POST")
            return redirect(url_for('generate'))
        try:
            totp = pyotp.TOTP(secret_key)
            current_code = totp.now()
            remaining = 30 - (int(time.time()) % 30)
            logger.info("2FA code generated successfully for secret key")
            return render_template('generate.html', code=current_code, remaining=remaining, secret_key=secret_key)
        except Exception as e:
            flash(f"Invalid secret key: {str(e)}", "error")
            logger.error("Error generating 2FA code: %s", str(e))
            return redirect(url_for('generate'))
    return render_template('generate.html')

@app.route('/get_2fa_code', methods=['POST'])
def get_2fa_code():
    """API endpoint to fetch 2FA code dynamically."""
    logger.info("Accessing /get_2fa_code route")
    secret_key = request.form.get('secret_key', '').strip().replace(" ", "")
    try:
        totp = pyotp.TOTP(secret_key)
        current_code = totp.now()
        remaining = 30 - (int(time.time()) % 30)
        return jsonify({'code': current_code, 'remaining': remaining})
    except Exception as e:
        logger.error("Error fetching 2FA code: %s", str(e))
        return jsonify({'error': str(e)}), 400

@app.route('/save', methods=['GET', 'POST'])
def save():
    """Save UID, password, and 2FA key."""
    logger.info("Accessing /save route: %s", request.method)
    if request.method == 'POST':
        password = get_default_password()
        if not password:
            flash("No default password set! Please set one first.", "error")
            logger.warning("No default password set, redirecting to /set_password")
            return redirect(url_for('set_password'))
        
        uid = request.form.get('uid', '').strip()
        secret_key = request.form.get('secret_key', '').strip().replace(" ", "")
        
        if not uid or not secret_key:
            flash("UID and secret key cannot be empty!", "error")
            logger.warning("UID or secret key empty on /save POST")
            return redirect(url_for('save'))
        
        try:
            totp = pyotp.TOTP(secret_key)
            current_code = totp.now()
            
            with open(ID_AUTO_CREATE_FILE, 'a') as f:
                f.write(f"{uid}|{password}|{secret_key}\n")
                f.flush()
            os.chmod(ID_AUTO_CREATE_FILE, 0o644)
            logger.info("Saved UID and secret key to Id_Auto_Creat.txt")
            
            with open(KEY_FILE, "w") as f:
                f.write(secret_key)
                f.flush()
            os.chmod(KEY_FILE, 0o644)
            logger.info("Saved secret key to 2fa_key.txt")
            
            flash("Data saved successfully!", "success")
            remaining = 30 - (int(time.time()) % 30)
            return render_template('save.html', code=current_code, remaining=remaining, uid=uid, secret_key=secret_key)
        except Exception as e:
            flash(f"Error saving data: {str(e)}", "error")
            logger.error("Error saving data: %s", str(e))
            return redirect(url_for('save'))
    return render_template('save.html')

@app.route('/set_password', methods=['GET', 'POST'])
def set_password():
    """Set or update the default password."""
    logger.info("Accessing /set_password route: %s", request.method)
    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        if not password:
            flash("Password cannot be empty!", "error")
            logger.warning("Password empty on /set_password POST")
            return redirect(url_for('set_password'))
        
        if get_default_password():
            change = request.form.get('change', 'n').strip().lower()
            if change != 'y':
                flash("Password change cancelled.", "info")
                logger.info("Password change cancelled")
                return redirect(url_for('index'))
        
        try:
            with open(DEFAULT_PASSWORD_FILE, "w") as f:
                f.write(password)
                f.flush()
            os.chmod(DEFAULT_PASSWORD_FILE, 0o644)
            flash("Default password saved successfully!", "success")
            logger.info("Default password saved successfully")
            return redirect(url_for('index'))
        except Exception as e:
            flash(f"Error saving password: {str(e)}", "error")
            logger.error("Error saving password: %s", str(e))
            return redirect(url_for('set_password'))
    
    try:
        default_password = get_default_password()
        logger.info("Rendering set_password.html with default_password=%s", bool(default_password))
        return render_template('set_password.html', default_password=default_password)
    except Exception as e:
        logger.error("Error rendering set_password.html: %s", str(e))
        flash("An error occurred while loading the page.", "error")
        return redirect(url_for('index'))

if __name__ == '__main__':
    # Local development
    logger.info("Starting Flask development server")
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=False)
else:
    # Production with Gunicorn
    logger.info("Starting Flask app for production (Gunicorn)")
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
