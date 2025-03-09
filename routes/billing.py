import requests
from config import Config
from flask import render_template, request, redirect, url_for
from ..db import db, Billing, calculate_billing_amount
from models import db, Billing, Customer, API, APIPricing
from datetime import datetime
import logging


@admin_bp.route('/update-pricing', methods=['POST'])
def update_pricing():
    """Allow admin to update API pricing dynamically."""
    data = request.json
    api_id = data.get('api_id')
    price = data.get('price')
    currency = data.get('currency', 'USD')

    api_pricing = APIPricing.query.filter_by(api_id=api_id).first()
    if api_pricing:
        api_pricing.price = price
        api_pricing.currency = currency
    else:
        new_price = APIPricing(api_id=api_id, price=price, currency=currency)
        db.session.add(new_price)

    db.session.commit()
    return jsonify({"message": "Pricing updated successfully"}), 200

def calculate_billing(api_id, usage_count, frequency):
    """Calculate API billing cost based on dynamic pricing set by the admin."""
    # Fetch pricing for the given API
    pricing = APIPricing.query.filter_by(api_id=api_id).first()

    if not pricing:
        raise ValueError(f"Pricing not set for API ID {api_id}. Please configure pricing in the admin panel.")

    # Get price based on frequency
    price = getattr(pricing, frequency, None)

    if price is None:
        raise ValueError(f"Invalid frequency '{frequency}'. Please provide a valid frequency.")

    total_amount = usage_count * price
    return {
        "api_id": api_id,
        "usage_count": usage_count,
        "frequency": frequency,
        "currency": pricing.currency,
        "total_amount": total_amount
    }



def save_billing_info(customer_id, api_id, frequency, price, currency, total_amount):
    """Save billing information to the database."""
    new_billing = Billing(
        customer_id=customer_id,
        api_id=api_id,
        frequency=frequency,
        price=price,
        currency=currency,
        total_amount=total_amount,
    )

    db.session.add(new_billing)
    db.session.commit()
    logging.info(f"Billing information saved for customer {customer_id}. Amount: {total_amount}")
    return new_billing


def send_billing_info_to_erp(user, amount, erp_system):
    """Send billing data to an ERP system."""
    try:
        url = Config.ERP_SYSTEMS.get(erp_system)

        if not url:
            raise ValueError(f"ERP system URL for {erp_system} not found in configuration.")

        # Sending the billing info as a POST request
        response = requests.post(url, json={"user": user, "amount": amount})

        # Check if the response was successful (HTTP status code 200)
        if response.status_code == 200:
            return response.json()  # Return response data
        else:
            logging.error(f"Failed to send billing info for user {user}. Status code: {response.status_code}")
            return {"error": "Failed to send data"}

    except requests.RequestException as e:
        logging.error(f"Request failed for user {user}: {e}")
        return {"error": str(e)}
    except Exception as e:
        logging.error(f"Error sending billing info for user {user}: {e}")
        return {"error": str(e)}


    }