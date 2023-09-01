from flask import render_template, request, redirect, url_for, flash, request
from Shop import app, db, cloudinary, bcrypt
from Shop.forms import RegistrationForm, LoginForm
from Shop.models import User, Data
from flask_login import login_user, current_user, logout_user, login_required
import random
from flask_mail import Message
from Shop import mail


# Creating random One-Time-Password
OTP = random.randint(1000, 9999)


# Creating the Homepage route
@app.route('/')
def Index():
    all_data = []
    if current_user.is_authenticated:
        all_data = Data.query.filter_by(user_id=current_user.id).all()
    else:
        pass
    return render_template("index.html", items=all_data[::-1])


# Creating the add-item route
@app.route('/insert', methods=['POST'])
@login_required
def insert():
    if request.method == 'POST':
        name = request.form['name']
        quantity = request.form['quantity']
        new_item = Data(name=name,  quantity=quantity, user_id=current_user.id)
        
        
    if 'image' in request.files:
        image = request.files['image']
        if image:
            upload_result = cloudinary.uploader.upload(image)
            image_url = upload_result['url']
            new_item.image_url = image_url   
        
        
        if not name or not quantity:
            flash("Please enter all fields!")
            return redirect(url_for('Index'))
        
    # if 'image' in request.files:
    #     image = request.files['image']
    #     if image:
    #         upload_result = cloudinary.uploader.upload(image)
    #         image_url = upload_result['url']
    #         new_item.image_url = image_url   
        
        

        db.session.add(new_item)
        db.session.commit()

        flash("Item Added To Cart", 'success')
        return redirect(url_for('Index'))
    
    

# Creating the update-item route
@app.route('/update', methods=['POST'])
def update():
    if request.method == 'POST':
        item = Data.query.get(request.form.get('id'))
        
        if not item:
            flash("item not found!")
            return redirect(url_for('index'))

        item.name = request.form['name']
        # item.price = request.form['price']
        item.quantity = request.form['quantity']
        db.session.commit()

        flash("Item Updated Successfully", 'success')
        return redirect(url_for('Index'))
    
    
# Creating the delete-item  route
@app.route('/delete/<int:id>/', methods=['GET', 'POST'])
def delete(id):
    item = Data.query.get(id)
    if not item:
        flash("Item not found!")
        return redirect(url_for('Index'))

    db.session.delete(item)
    db.session.commit()
    flash("Item Deleted Successfully", 'success')
    return redirect(url_for('Index'))



# Creating the register-user route
@app.route('/register', methods=['GET', 'POST'])
def register():
# Preventing the user from logging in again if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('Index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        send_otp(form.email.data)
        flash(f'Please verify your email', 'success')
        return redirect(url_for('verify_otp', email=form.email.data))
    return render_template('register.html', title='Register', form=form)


# Creating the OTP email
def send_otp(email):
    msg = Message('Verification Token', sender='Anonymous@gmail.com', recipients=[email])
    msg.body = f'Your verification token is: {OTP}'
    mail.send(msg)



# Creating the login route
@app.route('/login', methods=['GET', 'POST'])
def login():

# Preventing the user from logging in again if already logged in

    if current_user.is_authenticated:
        return redirect(url_for('Index'))
    form = LoginForm()
    if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if not user:
                flash('Invalid email', 'danger')
                return redirect(url_for('login'))
            if not user.is_verified:
                flash('You are yet to be verified', 'danger')
                send_otp(form.email.data)
                return redirect(url_for('verify_otp', email=form.email.data))
            if user and bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')
                flash(f'You have been logged in!', 'success')
                if user.is_admin:
                    return redirect('admin_view')    
                return redirect(next_page) if next_page  else redirect(url_for('Index'))
            else:
                flash('Login Unsuccessful. Please check email and password', 'danger')
            print('Login Failed')
    return render_template('login.html', title='Login', form=form)


# Creating the logout route
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('Index'))


# Creating the user-items route
@app.route('/items',  methods=['GET', 'POST'])
@login_required
def items():
    all_data = Data.query.filter_by(user_id=current_user.id).all()
    return render_template("items.html", items=all_data[::-1])
    
    


# Creating the admin route 
@app.route('/admin_users', methods=['GET', 'POST'])
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('You are not authorized to view this page!', 'danger')
        return redirect(url_for('Index'))
    else:
        users = User.query.all()
    return render_template('admin_users.html', users=users)


# Creating the admin route for viewing users
@app.route('/admin_view', methods=['GET', 'POST'])
def admin_view():
    if not current_user.is_admin:
        flash('You are not authorized to perform this action!', 'danger')
        return redirect(url_for('Index'))
    users = User.query.all()
    return render_template('admin_users.html', users=users)


# Creating the admin route for deleting users
@app.route('/admin/delete_user/<int:user_id>/', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if not current_user.is_admin:
        flash('You are not authorized to perform this action!', 'danger')
        return redirect(url_for('admin_users'))

    user = User.query.get(user_id)
    if not user:
        flash('User not found!', 'danger')
        return redirect(url_for('admin_users'))
    
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin_users'))



# Creating the admin route for viewing user-items
@app.route('/admin/view_user_items/<int:user_id>/', methods=['GET'])
@login_required
def view_user_items(user_id):
    if not current_user.is_admin:
        flash('You are not authorized to view this page!', 'danger')
        return redirect(url_for('admin_users'))

    user = User.query.get(user_id)
    if not user:
        flash('User not found!', 'danger')
        return redirect(url_for('admin_users'))
    
    items = Data.query.filter_by(user_id=user.id).all()
    return render_template('user_items.html', items=items, user=user)



# Creating the verify OTP for registering users
@app.route('/verify_otp/<string:email>/', methods=['GET', 'POST'])
def verify_otp(email):
    if request.method == 'POST':
        otp = request.form.get('otp')
        user = User.query.filter_by(email=email).first()
        if int(otp) != OTP:
            flash('Invalid OTP', 'danger')
            return redirect(url_for('verify_otp', email=email))
        user.is_verified = True
        db.session.commit()
        flash('Email verified successfully', 'success')
        return redirect(url_for('login'))
    return render_template('otp.html')