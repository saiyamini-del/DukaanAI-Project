"""
whatsapp_helper.py - Generates WhatsApp payment reminder messages and click-to-chat links
in clean English for Dukaan AI.
"""

import urllib.parse

def generate_whatsapp_link(phone: str, customer_name: str, balance: float, shop_name: str, owner_name: str, upi_id: str) -> str:
    """
    Generate a direct wa.me URL with a pre-filled, polite English payment reminder message.
    """
    if not phone:
        return ""

    # Clean phone number (add 91 if 10-digit Indian mobile number)
    clean_phone = "".join(filter(str.isdigit, phone))
    if len(clean_phone) == 10:
        clean_phone = "91" + clean_phone

    message = (
        f"Dear {customer_name},\n\n"
        f"This is a gentle payment reminder from {shop_name}.\n"
        f"Your current outstanding balance is ₹{balance:,.2f}.\n\n"
        f"💳 Pay easily via UPI ID: {upi_id}\n"
        f"You can also settle this in cash during your next store visit.\n\n"
        f"Thank you for your business!\n"
        f"— {owner_name}\n"
        f"Contact: {clean_phone}"
    )

    encoded_msg = urllib.parse.quote(message)
    return f"https://wa.me/{clean_phone}?text={encoded_msg}"
