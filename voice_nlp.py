"""
voice_nlp.py - English Voice and Text NLP Parser for Dukaan AI.
Extracts: Customer Name, Amount, Transaction Type (GIVEN vs RECEIVED), and Notes.
"""

import re
from typing import Dict, Any, Optional, List

# English keywords for credit given (Credit out / Shopkeeper gave goods on loan / Udhar)
GIVEN_KEYWORDS = [
    "gave", "give", "given", "credit", "credited", "due", "borrowed", "lent", "lend",
    "debit", "debited", "loan", "loaned", "took", "bought on credit", "pending"
]

# English keywords for payment received (Cash in / Customer repaid debt / Settlement)
RECEIVED_KEYWORDS = [
    "received", "got", "paid", "repaid", "settled", "collected", "repayment", "cleared",
    "deposited", "cash received", "upi payment", "gpay", "phonepe", "paytm", "settlement"
]

# Common English number words
ENGLISH_NUMBER_WORDS = {
    "fifty": 50, "hundred": 100, "one hundred": 100, "two hundred": 200, "three hundred": 300,
    "four hundred": 400, "five hundred": 500, "six hundred": 600, "seven hundred": 700,
    "eight hundred": 800, "nine hundred": 900, "one thousand": 1000, "thousand": 1000,
    "two thousand": 2000, "fifteen hundred": 1500, "twenty five hundred": 2500
}

# Stopwords & filler tokens to clean from names and notes
ENGLISH_STOPWORDS = [
    "to", "from", "for", "of", "in", "by", "on", "at", "the", "a", "an", "and",
    "rs", "rupees", "inr", "₹", "bucks", "cash", "amount", "money", "via", "through"
]

# Common retail grocery and store items
GROCERY_KEYWORDS = [
    "milk", "rice", "dal", "oil", "cooking", "refined", "sugar", "tea", "coffee", "soap", "paste", "eggs", "biscuit",
    "biscuits", "groceries", "bread", "butter", "cheese", "flour", "wheat", "atta", "spices",
    "salt", "maggi", "noodles", "chocolates", "chips", "drinks", "water", "detergent", "shampoo",
    "packet", "bottle", "box", "kg", "liter", "items", "bill", "provisions"
]

def extract_amount(text: str) -> Optional[float]:
    """Extract numeric amount or English number words from text."""
    text_lower = text.lower()

    # Check word numbers
    for phrase, val in ENGLISH_NUMBER_WORDS.items():
        if re.search(rf"\b{re.escape(phrase)}\b", text_lower):
            return float(val)

    # Standard digits (e.g. 500, 1,200, ₹450, 450.50, 500/-)
    matches = re.findall(r"(?:₹|rs\.?|inr|\$)?\s*(\d+(?:,\d+)*(?:\.\d{1,2})?)\s*(?:/-|rupees)?", text, re.IGNORECASE)
    if matches:
        clean_num = matches[0].replace(",", "")
        try:
            return float(clean_num)
        except ValueError:
            pass

    # Standalone numbers
    fallback = re.findall(r"\b\d+\b", text)
    if fallback:
        return float(fallback[0])

    return None

def determine_transaction_type(text: str) -> str:
    """
    Determine whether transaction is:
    - GIVEN (Credit to customer - shop will collect later)
    - RECEIVED (Cash/payment collected - debt settled)
    """
    text_lower = text.lower()

    # Check RECEIVED keywords first
    for kw in RECEIVED_KEYWORDS:
        if re.search(rf"\b{re.escape(kw)}\b", text_lower):
            return "RECEIVED"

    # Check GIVEN keywords
    for kw in GIVEN_KEYWORDS:
        if re.search(rf"\b{re.escape(kw)}\b", text_lower):
            return "GIVEN"

    return "GIVEN"

def extract_customer_and_note(text: str, amount: Optional[float], trans_type: str, known_customers: list = None) -> tuple:
    """
    Extract customer name and any item/goods note from English voice transcript.
    Matches against known customers first if available.
    """
    text_clean = text.strip()

    # 1. Match against known customers first
    if known_customers:
        for c in known_customers:
            cust_name = c["name"].strip()
            first_name = cust_name.split()[0]
            # Exact match for full name or first name
            if re.search(rf"\b{re.escape(cust_name)}\b", text_clean, re.IGNORECASE):
                note_candidate = re.sub(rf"\b{re.escape(cust_name)}\b", " ", text_clean, flags=re.IGNORECASE)
                note = clean_note_text(note_candidate, amount)
                return cust_name, note
            elif first_name and re.search(rf"\b{re.escape(first_name)}\b", text_clean, re.IGNORECASE):
                note_candidate = re.sub(rf"\b{re.escape(first_name)}\b", " ", text_clean, flags=re.IGNORECASE)
                note = clean_note_text(note_candidate, amount)
                return cust_name, note

    # 2. Heuristic extraction for English commands
    # Replace amount digits with a single space to avoid word concatenation
    if amount:
        text_without_amount = re.sub(rf"(?:₹|rs\.?|inr|\$)?\s*{int(amount)}(?:\.0+)?\s*(?:/-)?", " ", text_clean, flags=re.IGNORECASE)
    else:
        text_without_amount = text_clean

    all_action_words = set([w.lower() for w in GIVEN_KEYWORDS + RECEIVED_KEYWORDS + ENGLISH_STOPWORDS])

    words = text_without_amount.split()
    name_tokens = []
    note_tokens = []

    for word in words:
        clean_word = re.sub(r"[^\w\s]", "", word).strip()
        if not clean_word:
            continue

        lower_word = clean_word.lower()

        if lower_word in all_action_words:
            continue

        # If it matches known grocery items, add to notes
        if any(item in lower_word for item in GROCERY_KEYWORDS):
            note_tokens.append(word)
        elif len(name_tokens) < 2:
            # First 1-2 capitalized or non-action words are treated as the customer name
            name_tokens.append(clean_word.capitalize())
        else:
            note_tokens.append(word)

    customer_name = " ".join(name_tokens).strip() if name_tokens else "Customer"
    note = " ".join(note_tokens).strip()

    return customer_name, note

def clean_note_text(text: str, amount: Optional[float]) -> str:
    """Clean leftover markers and stopwords from note text."""
    if not text:
        return ""
    if amount:
        text = re.sub(rf"(?:₹|rs\.?|inr|\$)?\s*{int(amount)}(?:\.0+)?\s*(?:/-)?", " ", text, flags=re.IGNORECASE)

    all_strip = GIVEN_KEYWORDS + RECEIVED_KEYWORDS + ENGLISH_STOPWORDS
    for kw in all_strip:
        text = re.sub(rf"\b{re.escape(kw)}\b", " ", text, flags=re.IGNORECASE)

    text = re.sub(r"[\s\-_,]+", " ", text).strip()
    return text.capitalize() if text else ""

def parse_voice_command(transcript: str, known_customers: list = None) -> Dict[str, Any]:
    """
    Main entry point for parsing English voice or text transcripts.
    Returns structured transaction dictionary with confidence and explanatory breakdown.
    """
    if not transcript or not transcript.strip():
        return {
            "success": False,
            "error": "Empty transcript received"
        }

    amount = extract_amount(transcript)
    trans_type = determine_transaction_type(transcript)
    customer_name, note = extract_customer_and_note(transcript, amount, trans_type, known_customers)

    # Calculate confidence score
    confidence = 50
    if amount and amount > 0:
        confidence += 25
    if customer_name and customer_name != "Customer":
        confidence += 15
    if trans_type in ["GIVEN", "RECEIVED"]:
        confidence += 10

    type_label = "Credit Given (You will collect)" if trans_type == "GIVEN" else "Payment Received (Cash Collected)"
    type_badge = "🔴 Credit Given (Udhar)" if trans_type == "GIVEN" else "🟢 Payment Received (Cash In)"

    explanation = f"{customer_name} – {type_label} of ₹{amount if amount else 0:,.2f}"
    if note:
        explanation += f" for {note}"

    return {
        "success": True,
        "transcript": transcript,
        "language": "English",
        "customer_name": customer_name,
        "amount": amount if amount else 0.0,
        "type": trans_type,
        "type_badge": type_badge,
        "type_label": type_label,
        "note": note,
        "confidence": confidence,
        "explanation": explanation
    }

if __name__ == "__main__":
    test_phrases = [
        "Gave 500 to Ramesh for rice and dal",
        "Received 300 from Suresh",
        "Ramesh credit 200 for milk",
        "Received 1200 from Venkat Rao cash payment",
        "Gave 450 to Rahul Sharma for groceries",
        "Pooja Patel paid 500 complete balance",
        "Lent 650 to Shiva for cooking oil"
    ]
    print("Testing English NLP Voice Parser:")
    for p in test_phrases:
        res = parse_voice_command(p)
        print(f"\nInput: '{p}'")
        print(f" -> Customer: {res['customer_name']} | Amount: ₹{res['amount']} | Type: {res['type']} | Note: {res['note']}")
