from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf import CSRFProtect
from models import db, User, VaultItem
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from utils import encrypt_password, decrypt_password
from forms import RegisterForm, LoginForm, VaultItemForm, VaultItemEditForm, DeleteForm
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")  # Make sure this is set in your .env

app.config.from_object('config.Config')
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

csrf = CSRFProtect(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    return "Family Vault App is running!"


@app.route('/vault-check')
@login_required
def vault_check():
    items = VaultItem.query.filter_by(user_id=current_user.id).all()
    return {
        "user": current_user.email,
        "items": [
            {
                "site": item.site_name,
                "username": item.username,
                "password": decrypt_password(item.encrypted_password)
            } for item in items
        ]
    }

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = generate_password_hash(form.password.data)

        new_user = User(name=name, email=email, hashed_password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("Account created successfully! You can log in now.", "success")
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.hashed_password, password):
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for('vault'))
        else:
            flash("Invalid login credentials.", "danger")
    return render_template('login.html', form=form)


@app.route('/vault', methods=['GET', 'POST'])
@login_required
def vault():
    form = VaultItemForm()
    delete_form = DeleteForm()

    if form.validate_on_submit():
        site = form.site_name.data
        username = form.username.data
        password = form.password.data
        encrypted = encrypt_password(password)

        item = VaultItem(
            user_id=current_user.id,
            site_name=site,
            username=username,
            encrypted_password=encrypted
        )
        db.session.add(item)
        db.session.commit()
        flash(f"{site} credentials saved to your vault!", "success")
        return redirect(url_for('vault'))

    vault_items = VaultItem.query.filter_by(user_id=current_user.id).all()
    print(f"[DEBUG] Loaded {len(vault_items)} items for user {current_user.id}")
    for item in vault_items:
        item.decrypted_password = decrypt_password(item.encrypted_password)
        print(f"[DEBUG] Site: {item.site_name}, Username: {item.username}, Password: {item.encrypted_password}")

    return render_template('vault.html', vault_items=vault_items, form=form, delete_form=delete_form)
    



@app.route('/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    form = DeleteForm()
    if form.validate_on_submit():
        item = VaultItem.query.get_or_404(item_id)
        if item.user_id != current_user.id:
            flash("Unauthorized action.", "danger")
            return redirect(url_for('vault'))

        db.session.delete(item)
        db.session.commit()
        flash(f"{item.site_name} removed from your vault.", "info")

    return redirect(url_for('vault'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You've been logged out.", "info")
    return redirect(url_for('login'))


@app.route('/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = VaultItem.query.get(item_id)
    if item.user_id != current_user.id:
        return "Unauthorized", 403

    form = VaultItemEditForm(obj=item)
    if form.validate_on_submit():
        item.site_name = form.site_name.data
        item.username = form.username.data
        item.encrypted_password = encrypt_password(form.password.data)
        db.session.commit()
        flash(f"{item.site_name} credentials updated!", "success")
        return redirect(url_for('vault'))

    form.password.data = decrypt_password(item.encrypted_password)
    return render_template('edit.html', form=form, item=item)
    

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
