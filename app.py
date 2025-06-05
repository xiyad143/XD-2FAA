from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import os
import pyotp
import time

app = Flask(__name__)
app.secret_key = "super-secret-key-2fa"

# Directory for storing data files
DATA_DIR = os.path.join(os.getcwd(), "data")
DEFAULT_PASSWORD_FILE = os.path.join(DATA_DIR, "default_password.txt")
ID_AUTO_CREATE_FILE = os.path.join(DATA_DIR, "Id_Auto_Creat.txt")
KEY_FILE = os.path.join(DATA_DIR, "2fa_key.txt")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

def get_default_password():
    """Read the default password from file."""
    if os.path.exists(DEFAULT_PASSWORD_FILE):
        with open(DEFAULT_PASSWORD_FILE, "r") as f:
            return f.read().strip()
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
            flash(f"Error: {str(e)}", "error")
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
            # Validate the secret key
            totp = pyotp.TOTP(secret_key)
            current_code = totp.now()
            
            # Save UID, password, and 2FA key
            with open(ID_AUTO_CREATE_FILE, 'a') as f:
                f.write(f"{uid}|{password}|{secret_key}\n")
            
            # Save 2FA key separately
            key_path = KEY_FILE
            os.makedirs(os.path.dirname(key_path), exist_ok=True)
            with open(key_path, "w") as f:
                f.write(secret_key)
            
            flash("Data saved successfully!", "success")
            remaining = 30 - (int(time.time()) % 30)
            return render_template('save.html', code=current_code, remaining=remaining, uid=uid, secret_key=secret_key)
        except Exception as e:
            flash(f"Error: {str(e)}", "error")
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
        
        # Check if default password already exists
        if get_default_password():
            change = request.form.get('change', 'n').strip().lower()
            if change != 'y':
                flash("Password change cancelled.", "info")
                return redirect(url_for('index'))
        
        # Save the new password
        try:
            with open(DEFAULT_PASSWORD_FILE, "w") as f:
                f.write(password)
            flash("Default password saved successfully!", "success")
            return redirect(url_for('index'))
        except Exception as e:
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for('set_password'))
    
    default_password = get_default_password()
    return render_template('set_password.html', default_password=default_password)

if __name__ == '__main__':
    app.run(debug=True)