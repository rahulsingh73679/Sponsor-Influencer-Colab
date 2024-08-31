from flask import Flask, request, render_template, redirect, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import bcrypt
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.secret_key = 'your_secret_key'  # Change this to something more secure
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(50))
    is_flagged = db.Column(db.Boolean, default=False)  # Added is_flagged column

    def __init__(self, name, email, password, role):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        self.role = role

    def verify_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    budget = db.Column(db.Float)
    visibility = db.Column(db.String(50))
    goals = db.Column(db.String(200))
    sponsor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    sponsor = db.relationship('User', backref=db.backref('campaigns', lazy=True))
    is_flagged = db.Column(db.Boolean, default=False)  # Added is_flagged column

class AdRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'))
    influencer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    messages = db.Column(db.String(500))
    requirements = db.Column(db.String(500))
    payment_amount = db.Column(db.Float)
    status = db.Column(db.String(15), default='pending')
    campaign = db.relationship('Campaign', backref=db.backref('ad_requests', lazy=True))
    influencer = db.relationship('User', backref=db.backref('ad_requests', lazy=True))
    is_flagged = db.Column(db.Boolean, default=False)  # Added is_flagged column

# Index Route
@app.route('/')
def index():
    return redirect('/register')

# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        if not all([name, email, password, role]):
            flash('All fields are required.')
            return redirect('/register')

        if User.query.filter_by(email=email).first():
            flash('Email already in use.')
            return redirect('/register')

        new_user = User(name=name, email=email, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please log in.')
        return redirect('/login')

    return render_template('register.html')

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        if user and user.verify_password(password):
            session['email'] = email
            session['user_id'] = user.id
            session['role'] = user.role
            return redirect('/dashboard')

        flash('Invalid email or password.')
        return redirect('/login')

    return render_template('login.html')

# User Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect('/login')

# Updated Dashboard Route
@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        return redirect('/login')

    user_role = session.get('role')
    if user_role == 'admin':
        # Count total users based on roles
        admin_count = User.query.filter_by(role='admin').count()
        sponsor_count = User.query.filter_by(role='sponsor').count()
        influencer_count = User.query.filter_by(role='influencer').count()
        
        # Count total campaigns and ad requests
        campaign_count = Campaign.query.count()
        ad_request_count = AdRequest.query.count()
        
        # Fetch all campaigns and ad requests
        campaigns = Campaign.query.all()
        ad_requests = AdRequest.query.all()
        
        # Fetch all users except admin
        users = User.query.filter(User.role != 'admin').all()

        return render_template('admin_dashboard.html', 
                               admin_count=admin_count, 
                               sponsor_count=sponsor_count, 
                               influencer_count=influencer_count, 
                               campaign_count=campaign_count, 
                               ad_request_count=ad_request_count, 
                               campaigns=campaigns,
                               ad_requests=ad_requests,
                               users=users)
    elif user_role == 'sponsor':
        sponsor_id = session.get('user_id')
        campaigns = Campaign.query.filter_by(sponsor_id=sponsor_id).all()
        ad_requests = AdRequest.query.join(Campaign).filter(Campaign.sponsor_id == sponsor_id).all()
        return render_template('sponsor_dashboard.html', campaigns=campaigns, ad_requests=ad_requests)
    elif user_role == 'influencer':
        influencer_id = session.get('user_id')
        ad_requests = AdRequest.query.filter_by(influencer_id=influencer_id).all()
        campaign_ids = [ad_request.campaign_id for ad_request in ad_requests]
        campaigns = Campaign.query.filter(Campaign.id.in_(campaign_ids)).all()
        return render_template('influencer_dashboard.html', ad_requests=ad_requests, campaigns=campaigns)

    return redirect('/login')



# Added Search Functionality
@app.route('/search/campaigns', methods=['GET'])
def search_campaigns():
    visibility = request.args.get('visibility', '')
    campaigns = Campaign.query.filter_by(visibility=visibility).all()
    return render_template('search_campaigns.html', campaigns=campaigns)


@app.route('/search/influencers', methods=['GET'])
def search_influencers():
    category = request.args.get('category', '')
    influencers = User.query.filter_by(role='influencer').filter(User.name.like(f'%{category}%')).all()
    return render_template('search_influencers.html', influencers=influencers)




# Route to flag/unflag a user
@app.route('/user/flag/<int:user_id>', methods=['POST'])
def flag_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_flagged = not user.is_flagged
    db.session.commit()
    return redirect('/dashboard')

# Route to delete a user
@app.route('/user/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect('/dashboard')

# Route to flag/unflag a campaign
@app.route('/campaign/flag/<int:campaign_id>', methods=['POST'])
def flag_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    campaign.is_flagged = not campaign.is_flagged
    db.session.commit()
    return redirect('/dashboard')

# Route to delete a campaign
@app.route('/campaign/delete/<int:campaign_id>', methods=['POST'])
def delete_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    db.session.delete(campaign)
    db.session.commit()
    return redirect('/dashboard')

# Route to flag/unflag an ad request
@app.route('/ad_request/flag/<int:ad_request_id>', methods=['POST'])
def flag_ad_request(ad_request_id):
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    ad_request.is_flagged = not ad_request.is_flagged
    db.session.commit()
    return redirect('/dashboard')

# Route to delete an ad request
@app.route('/ad_request/delete/<int:ad_request_id>', methods=['POST'])
def delete_ad_request(ad_request_id):
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    db.session.delete(ad_request)
    db.session.commit()
    return redirect('/dashboard')

# Search Campaigns for Influencers
@app.route('/search/influencer_campaigns', methods=['GET'])
def influencer_search_campaigns():
    visibility = request.args.get('visibility', 'public')  # Default to public
    campaigns = Campaign.query.filter_by(visibility=visibility).all()
    return render_template('influencer_search_campaigns.html', campaigns=campaigns)

# Send Ad Request
@app.route('/send/ad_request/<int:campaign_id>', methods=['POST'])
def send_ad_request(campaign_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    payment_amount = request.form.get('payment_amount')
    if not payment_amount:
        flash('Payment amount is required.', 'error')
        return redirect(url_for('influencer_search_campaigns'))

    new_ad_request = AdRequest(
        influencer_id=user_id,
        campaign_id=campaign_id,
        status='Pending',
        messages='Request sent from influencer.',
        payment_amount=float(payment_amount)
    )
    db.session.add(new_ad_request)
    db.session.commit()

    flash('Ad request sent successfully', 'success')
    return redirect(url_for('influencer_search_campaigns'))





# Ad Request Management
@app.route('/ad_request/create', methods=['GET', 'POST'])
def create_ad_request():
    if request.method == 'POST':
        campaign_id = request.form['campaign_id']
        influencer_id = request.form['influencer_id']
        messages = request.form['messages']
        requirements = request.form['requirements']
        payment_amount = request.form['payment_amount']

        new_ad_request = AdRequest(
            campaign_id=campaign_id, 
            influencer_id=influencer_id, 
            messages=messages, 
            requirements=requirements, 
            payment_amount=payment_amount
        )
        db.session.add(new_ad_request)
        db.session.commit()
        return redirect('/dashboard')

    influencers = User.query.filter_by(role='influencer')
    campaigns = Campaign.query.filter_by(sponsor_id=session['user_id'])
    return render_template('create_ad_request.html', campaigns=campaigns, influencers=influencers)


@app.route('/ad_request/action/<int:ad_request_id>', methods=['GET', 'POST'])
def ad_request_action(ad_request_id):
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    
    if request.method == 'POST':
        action = request.form['action']
        if action == 'accept':
            ad_request.status = 'accepted'
        elif action == 'reject':
            ad_request.status = 'rejected'
        elif action == 'negotiate':
            new_payment_amount = request.form['new_payment_amount']
            ad_request.payment_amount = float(new_payment_amount)
            ad_request.status = 'negotiation'
        
        db.session.commit()
        return redirect('/dashboard')

    return render_template('ad_request_action.html', ad_request=ad_request)











# Campaign Management
@app.route('/campaign/create', methods=['GET', 'POST'])
def create_campaign():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        budget = request.form['budget']
        visibility = request.form['visibility']
        goals = request.form['goals']
        sponsor_id = session['user_id']

        new_campaign = Campaign(
            name=name,
            description=description,
            start_date=datetime.strptime(start_date, '%Y-%m-%d'),
            end_date=datetime.strptime(end_date, '%Y-%m-%d'),
            budget=budget,
            visibility=visibility,
            goals=goals,
            sponsor_id=sponsor_id
        )

        db.session.add(new_campaign)
        db.session.commit()

        flash('Campaign created successfully', 'success')
        return redirect('/dashboard')

    return render_template('create_campaign.html')


# View and Manage Ad Requests
@app.route('/manage/ad_requests', methods=['GET'])
def manage_ad_requests():
    sponsor_id = session.get('user_id')
    ad_requests = AdRequest.query.join(Campaign).filter(Campaign.sponsor_id == sponsor_id).all()
    return render_template('manage_ad_requests.html', ad_requests=ad_requests)


# Route to update a campaign
@app.route('/campaign/update/<int:campaign_id>', methods=['GET', 'POST'])
def update_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    
    if request.method == 'POST':
        campaign.name = request.form.get('name', campaign.name)
        campaign.description = request.form.get('description', campaign.description)
        campaign.start_date = datetime.strptime(request.form.get('start_date', campaign.start_date.strftime('%Y-%m-%d')), '%Y-%m-%d')
        campaign.end_date = datetime.strptime(request.form.get('end_date', campaign.end_date.strftime('%Y-%m-%d')), '%Y-%m-%d')
        campaign.budget = float(request.form.get('budget', campaign.budget))
        campaign.visibility = request.form.get('visibility', campaign.visibility)
        campaign.goals = request.form.get('goals', campaign.goals)
        
        db.session.commit()
        flash('Campaign updated successfully', 'success')
        return redirect('/dashboard')

    return render_template('update_campaign.html', campaign=campaign)








if __name__ == '__main__':
    app.run(debug=True)
