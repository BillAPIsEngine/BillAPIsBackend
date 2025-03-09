from flask import Blueprint, request, render_template, session, redirect, url_for
import requests
import os
from werkzeug.utils import secure_filename
from config import Config
from db import get_db_connection
from logger import log_action
from routes.billing import calculate_billing, send_billing_info_to_erp
from routes.api_usage import fetch_api_details, fetch_datadog_usage, fetch_elk_usage
admin_bp = Blueprint('admin', __name__)
from flask import render_template, request, redirect, url_for, session
from ..db import db, Customer, User, API, CustomerAPI, LogConfig
from .logger import setup_logger


@app.route('/create_customer', methods=['GET', 'POST'])
def create_customer():
    if 'user' not in session or session['user'] != 'admin':
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        customer_name = request.form['customer_name']
        selected_apis = request.form.getlist('selected_apis')

        customer = Customer(name=customer_name)
        db.session.add(customer)
        db.session.commit()

        for api_id in selected_apis:
            customer_api = CustomerAPI(customer_id=customer.id, api_id=api_id)
            db.session.add(customer_api)

        db.session.commit()

        return redirect(url_for('admin.admin_portal'))

    apis = API.query.all()

    return render_template('create_customer.html', apis=apis)


@app.route('/create_user', methods=['GET', 'POST'])
def create_user():
    if 'user' not in session or session['user'] != 'admin':
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        customer_id = request.form['customer_id']

        user = User(username=username, password_hash=password, customer_id=customer_id)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('admin.admin_portal'))

    customers = Customer.query.all()

    return render_template('create_user.html', customers=customers)


# Predefined Billing Logic
# Predefined Billing Logic (without hardcoded rates)
BILLING_LOGICS = {
    "per_request": {"description": "Charge per API request"},
    "per_mb": {"description": "Charge per MB transferred"},
    "subscription": {"description": "Fixed monthly subscription"}
}

# Store API-to-billing assignments
API_BILLING_ASSIGNMENTS = {}


@admin_bp.route('/admin', methods=['GET', 'POST'])
def admin_portal():
    if 'user' not in session or session['user'] != 'admin':
        return redirect(url_for('auth.login'))

    api_details = None
    selected_billing_logic = None
    assigned_apis = API_BILLING_ASSIGNMENTS

    if request.method == 'POST':
        selected_manager = request.form.get('api_manager')
        billing_logic = request.form.get('billing_logic')
        billing_price = request.form.get('billing_price')
        currency = request.form.get('currency')

        if selected_manager:
            api_details = fetch_api_details(selected_manager)

        if billing_logic and billing_price and currency:
            selected_billing_logic = BILLING_LOGICS.get(billing_logic)

        # Assign billing logic, price, and currency to selected APIs
        selected_apis = request.form.getlist('selected_apis')
        for api in selected_apis:
            API_BILLING_ASSIGNMENTS[api] = {
                "billing_logic": billing_logic,
                "price": float(billing_price),
                "currency": currency
            }

    return render_template('admin.html',
                           managers=Config.API_MANAGERS.keys(),
                           api_details=api_details,
                           billing_logics=BILLING_LOGICS,
                           assigned_apis=assigned_apis)


@admin_bp.route('/get_billing_assignments', methods=['GET'])
def get_billing_assignments():
    return jsonify(API_BILLING_ASSIGNMENTS)


invoice_template = """
<html>
    <head><title>Invoice</title></head>
    <body>
        <h1>Invoice for {{ user }}</h1>
        <p><strong>Date:</strong> {{ date }}</p>
        <p><strong>Total Amount:</strong> ${{ amount }}</p>
    </body>
</html>
"""

@admin_bp.route('/admin', methods=['GET', 'POST'])
def admin_portal():
    if 'user' not in session or session['user'] != 'admin':
        return redirect(url_for('auth.login'))

    global invoice_template
    api_details = None
    api_usage_data = None
    erp_response = None
    billing_amount = None

    price_mapping = session.get('price_mapping', Config.PRICE_MAPPING)

    if request.method == 'POST':
        selected_manager = request.form.get('api_manager')
        api_details = fetch_api_details(selected_manager)

        # Billing Frequency
        billing_frequency = request.form.get('billing_frequency', Config.DEFAULT_BILLING_FREQUENCY)

        # Fetch metrics
        if request.form.get('fetch_metrics'):
            api_usage_data = fetch_datadog_usage() if selected_manager == "Datadog" else fetch_elk_usage()

        # Billing Calculation
        if api_usage_data:
            billing_amount = calculate_billing(api_usage_data, billing_frequency, price_mapping)

        # Send billing to ERP
        if request.form.get('send_to_erp'):
            user = request.form.get('user')
            erp_system = request.form.get('erp_system')
            erp_response = send_billing_info_to_erp(user, billing_amount, erp_system)

        # Handle invoice template upload
        if 'file' in request.files:
            file = request.files['file']
            if file.filename and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS:
                filename = secure_filename(file.filename)
                file.save(os.path.join(Config.UPLOAD_FOLDER, filename))
                with open(os.path.join(Config.UPLOAD_FOLDER, filename), 'r') as f:
                    invoice_template = f.read()

        # Handle custom invoice HTML template
        if request.form.get('custom_html_template'):
            invoice_template = request.form['custom_html_template']

        # Save pricing updates
        if 'set_price' in request.form:
            session['price_mapping'] = {key: float(request.form[key + '_price']) for key in price_mapping}

    return render_template('admin.html', managers=Config.API_MANAGERS.keys(),
                           api_details=api_details, api_usage_data=api_usage_data,
                           billing_amount=billing_amount, erp_response=erp_response,
                           invoice_template=invoice_template, price_mapping=price_mapping)

@app.route('/configure_logging', methods=['GET', 'POST'])
def configure_logging():
    if 'user' not in session or session['user'] != 'admin':
        return redirect(url_for('auth.login'))

    log_config = LogConfig.query.first()

    if request.method == 'POST':
        log_to_file = 'log_to_file' in request.form
        log_to_db = 'log_to_db' in request.form
        log_level = request.form['log_level']

        if log_config:
            log_config.log_to_file = log_to_file
            log_config.log_to_db = log_to_db
            log_config.log_level = log_level
            db.session.commit()
        else:
            new_log_config = LogConfig(log_to_file=log_to_file, log_to_db=log_to_db, log_level=log_level)
            db.session.add(new_log_config)
            db.session.commit()

        # Reconfigure the logger dynamically based on the updated settings
        setup_logger()

        return redirect(url_for('admin.admin_portal'))

    return render_template('configure_logging.html', log_config=log_config)



@admin.route("/assign-billing/<int:customer_id>", methods=["GET"])
@login_required
def assign_billing(customer_id):
    """Render the billing assignment page with APIs subscribed by the customer."""
    customer = Customer.query.get_or_404(customer_id)
    subscribed_apis = Subscription.query.filter_by(customer_id=customer_id).all()

    api_data = []
    for sub in subscribed_apis:
        api = APIService.query.get(sub.api_id)
        api_data.append({
            "id": api.id,
            "name": api.name,
            "description": api.description
        })

    billing_logics = BillingLogic.query.all()  # Fetch available billing rules
    return render_template("assign_billing.html", customer=customer, apis=api_data, billing_logics=billing_logics)

@admin.route("/apply-billing/<int:customer_id>", methods=["POST"])
@login_required
def apply_billing(customer_id):
    """Apply a billing logic to selected APIs for a customer."""
    data = request.json
    selected_apis = data.get("apis", [])
    billing_logic_id = data.get("billing_logic")

    if not selected_apis or not billing_logic_id:
        return jsonify({"message": "Please select APIs and a billing logic."}), 400

    for api_id in selected_apis:
        billing_entry = BillingLogic(customer_id=customer_id, api_id=api_id, billing_logic_id=billing_logic_id)
        db.session.add(billing_entry)

    db.session.commit()
    return jsonify({"message": "Billing logic applied successfully!"})


