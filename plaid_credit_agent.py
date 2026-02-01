import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import json

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="Credit Decisioning Agent | Plaid Infrastructure",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CUSTOM STYLING
# =============================================================================
st.markdown("""
<style>
    /* Main theme colors - Plaid inspired */
    :root {
        --plaid-navy: #0A2540;        /* Trust, banking */
        --plaid-blue: #0055FF;        /* Primary action, intelligence */
        --plaid-teal: #14B8A6;        /* Real-time signals (calmer) */
        --plaid-bg: #F1F5F9;          /* App background */
        --success: #16A34A;
        --warning: #F59E0B;
        --danger: #DC2626;
        --muted-text: #475569;
    
        /* LIGHT SURFACE */
        --surface-bg: #FFFFFF;
        --surface-text-primary: #0F172A;
        --surface-text-secondary: #334155;
    }

    
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0A2540;
        margin-bottom: 0.2rem;
    }
    
    .sub-header {
        font-size: 1rem;
        color: var(--plaid-blue);
        font-weight: 500;
    }
    
    .metric-box {
        background: linear-gradient(135deg, var(--plaid-navy) 0%, #102E4A 100%);
        padding: 1.2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
    }
    
    .metric-label {
        font-size: 0.85rem;
        opacity: 0.9;
    }
    
    .decision-approved {
        background-color: var(--success);
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 700;
        font-size: 1.2rem;
        text-align: center;
    }
    
    .decision-denied {
        background-color: var(--danger);
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 700;
        font-size: 1.2rem;
        text-align: center;
    }
    
    .decision-review {
        background-color: var(--warning);
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 700;
        font-size: 1.2rem;
        text-align: center;
    }
    
    .agent-step {
        background-color: #F1F5F9;
        border-left: 4px solid var(--plaid-blue);
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    .plaid-api-badge {
        background-color: #00D4AA;
        color: #0A2540;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    
    .quote-box {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-left: 4px solid var(--plaid-blue);
        padding: 1rem;
        margin: 1rem 0;
        font-style: italic;
    }
    
    .data-source-tag {
        background-color: #E2E8F0;
        color: #334155;
        padding: 0.15rem 0.4rem;
        border-radius: 3px;
        font-size: 0.7rem;
        margin-right: 0.3rem;
    }
    
    .stApp {
        background-color: var(--plaid-bg);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Fix Streamlit bordered containers */
    div[data-testid="stContainer"] > div {
        background-color: white;
        border-radius: 14px;
        border: 1px solid #E2E8F0;
    }
    

</style>
""", unsafe_allow_html=True)

# =============================================================================
# SIMULATED PLAID DATA
# =============================================================================
# These represent real loan applications a lender would process
LOAN_APPLICATIONS = {
    "APP-2025-0847": {
        "business_name": "Bright Future LLC",
        "business_type": "E-commerce (Shopify)",
        "years_in_business": 3,
        "loan_amount": 75000,
        "loan_purpose": "Inventory Purchase",
        "owner_name": "Sarah Chen",
        "owner_fico": 720,
        "plaid_linked": True,
        "linked_accounts": [
            {"institution": "Chase", "name": "Business Checking", "type": "depository", "subtype": "checking", "balance": 34521.00, "account_id": "acc_chase_001"},
            {"institution": "Chase", "name": "Business Savings", "type": "depository", "subtype": "savings", "balance": 89200.00, "account_id": "acc_chase_002"},
            {"institution": "American Express", "name": "Business Gold Card", "type": "credit", "subtype": "credit card", "balance": -12400.00, "limit": 50000, "account_id": "acc_amex_001"}
        ],
        "transactions_90d": [
            {"date": "2025-01-27", "name": "STRIPE TRANSFER", "amount": 8420.00, "category": ["Transfer", "Credit"], "merchant": "Stripe"},
            {"date": "2025-01-26", "name": "GUSTO PAYROLL", "amount": -12500.00, "category": ["Transfer", "Payroll"], "merchant": "Gusto"},
            {"date": "2025-01-25", "name": "AWS SERVICES", "amount": -2340.00, "category": ["Service", "Software"], "merchant": "Amazon Web Services"},
            {"date": "2025-01-24", "name": "STRIPE TRANSFER", "amount": 6200.00, "category": ["Transfer", "Credit"], "merchant": "Stripe"},
            {"date": "2025-01-23", "name": "COMMERCIAL LEASE PMT", "amount": -4500.00, "category": ["Payment", "Rent"], "merchant": "Parkview Properties"},
            {"date": "2025-01-22", "name": "QUICKBOOKS SUBSCRIPTION", "amount": -85.00, "category": ["Service", "Software"], "merchant": "Intuit"},
            {"date": "2025-01-20", "name": "STRIPE TRANSFER", "amount": 11200.00, "category": ["Transfer", "Credit"], "merchant": "Stripe"},
            {"date": "2025-01-18", "name": "INVENTORY - ALIBABA", "amount": -18500.00, "category": ["Payment", "Merchandise"], "merchant": "Alibaba"},
            {"date": "2025-01-15", "name": "STRIPE TRANSFER", "amount": 9800.00, "category": ["Transfer", "Credit"], "merchant": "Stripe"},
            {"date": "2025-01-12", "name": "GUSTO PAYROLL", "amount": -12500.00, "category": ["Transfer", "Payroll"], "merchant": "Gusto"},
            {"date": "2025-01-10", "name": "FACEBOOK ADS", "amount": -3200.00, "category": ["Service", "Advertising"], "merchant": "Meta"},
            {"date": "2025-01-08", "name": "STRIPE TRANSFER", "amount": 7650.00, "category": ["Transfer", "Credit"], "merchant": "Stripe"},
        ],
        "bank_income": {
            "verified_income": 48000,  # Monthly
            "income_sources": [{"source": "Stripe", "monthly_avg": 43000, "confidence": 0.94}, {"source": "Other", "monthly_avg": 5000, "confidence": 0.78}],
            "income_stability": "HIGH",
            "months_of_history": 24
        },
        "risk_signals": {
            "nsf_overdraft_count_90d": 0,
            "negative_balance_days_90d": 0,
            "account_age_days": 1095,
            "fraud_signals": [],
            "beacon_network_flags": 0
        }
    },
    "APP-2025-0923": {
        "business_name": "QuickLaunch AI Inc",
        "business_type": "SaaS Startup",
        "years_in_business": 0.7,
        "loan_amount": 150000,
        "loan_purpose": "Working Capital / Runway Extension",
        "owner_name": "Marcus Johnson",
        "owner_fico": 695,
        "plaid_linked": True,
        "linked_accounts": [
            {"institution": "Mercury", "name": "Operating Account", "type": "depository", "subtype": "checking", "balance": 12890.00, "account_id": "acc_merc_001"},
            {"institution": "Brex", "name": "Corporate Card", "type": "credit", "subtype": "credit card", "balance": -28900.00, "limit": 75000, "account_id": "acc_brex_001"}
        ],
        "transactions_90d": [
            {"date": "2025-01-27", "name": "INVESTOR WIRE - SEED", "amount": 50000.00, "category": ["Transfer", "Credit"], "merchant": "Wire Transfer"},
            {"date": "2025-01-26", "name": "GUSTO PAYROLL", "amount": -18000.00, "category": ["Transfer", "Payroll"], "merchant": "Gusto"},
            {"date": "2025-01-24", "name": "GOOGLE CLOUD", "amount": -4200.00, "category": ["Service", "Software"], "merchant": "Google"},
            {"date": "2025-01-22", "name": "STRIPE PAYOUT", "amount": 4200.00, "category": ["Transfer", "Credit"], "merchant": "Stripe"},
            {"date": "2025-01-20", "name": "AWS SERVICES", "amount": -3200.00, "category": ["Service", "Software"], "merchant": "Amazon Web Services"},
            {"date": "2025-01-18", "name": "LINKEDIN ADS", "amount": -5500.00, "category": ["Service", "Advertising"], "merchant": "LinkedIn"},
            {"date": "2025-01-15", "name": "STRIPE PAYOUT", "amount": 3800.00, "category": ["Transfer", "Credit"], "merchant": "Stripe"},
            {"date": "2025-01-12", "name": "GUSTO PAYROLL", "amount": -18000.00, "category": ["Transfer", "Payroll"], "merchant": "Gusto"},
            {"date": "2025-01-10", "name": "OFFICE RENT", "amount": -6500.00, "category": ["Payment", "Rent"], "merchant": "WeWork"},
        ],
        "bank_income": {
            "verified_income": 22000,
            "income_sources": [{"source": "Stripe", "monthly_avg": 18000, "confidence": 0.82}, {"source": "Investor Funding", "monthly_avg": 50000, "confidence": 0.65}],
            "income_stability": "LOW",
            "months_of_history": 8
        },
        "risk_signals": {
            "nsf_overdraft_count_90d": 2,
            "negative_balance_days_90d": 5,
            "account_age_days": 240,
            "fraud_signals": [],
            "beacon_network_flags": 0
        }
    },
    "APP-2025-1042": {
        "business_name": "Riverside Dental Group",
        "business_type": "Healthcare / Dental Practice",
        "years_in_business": 7,
        "loan_amount": 250000,
        "loan_purpose": "Practice Expansion - New Location",
        "owner_name": "Dr. Amanda Reyes",
        "owner_fico": 780,
        "plaid_linked": True,
        "linked_accounts": [
            {"institution": "Bank of America", "name": "Business Checking", "type": "depository", "subtype": "checking", "balance": 156000.00, "account_id": "acc_bofa_001"},
            {"institution": "Bank of America", "name": "Money Market", "type": "depository", "subtype": "savings", "balance": 420000.00, "account_id": "acc_bofa_002"},
            {"institution": "Chase", "name": "Ink Business Unlimited", "type": "credit", "subtype": "credit card", "balance": -8200.00, "limit": 35000, "account_id": "acc_chase_003"}
        ],
        "transactions_90d": [
            {"date": "2025-01-27", "name": "INSURANCE REIMBURSEMENT - DELTA", "amount": 42000.00, "category": ["Transfer", "Credit"], "merchant": "Delta Dental"},
            {"date": "2025-01-26", "name": "ADP PAYROLL", "amount": -65000.00, "category": ["Transfer", "Payroll"], "merchant": "ADP"},
            {"date": "2025-01-25", "name": "PATIENT PAYMENTS - BATCH", "amount": 28500.00, "category": ["Transfer", "Credit"], "merchant": "Square"},
            {"date": "2025-01-24", "name": "HENRY SCHEIN - SUPPLIES", "amount": -12400.00, "category": ["Payment", "Merchandise"], "merchant": "Henry Schein"},
            {"date": "2025-01-23", "name": "INSURANCE REIMBURSEMENT - CIGNA", "amount": 38000.00, "category": ["Transfer", "Credit"], "merchant": "Cigna"},
            {"date": "2025-01-22", "name": "COMMERCIAL LEASE", "amount": -8500.00, "category": ["Payment", "Rent"], "merchant": "Riverside Plaza LLC"},
            {"date": "2025-01-20", "name": "INSURANCE REIMBURSEMENT - AETNA", "amount": 31000.00, "category": ["Transfer", "Credit"], "merchant": "Aetna"},
            {"date": "2025-01-18", "name": "PATTERSON DENTAL", "amount": -8900.00, "category": ["Payment", "Merchandise"], "merchant": "Patterson Dental"},
            {"date": "2025-01-15", "name": "PATIENT PAYMENTS - BATCH", "amount": 24200.00, "category": ["Transfer", "Credit"], "merchant": "Square"},
            {"date": "2025-01-12", "name": "ADP PAYROLL", "amount": -65000.00, "category": ["Transfer", "Payroll"], "merchant": "ADP"},
        ],
        "bank_income": {
            "verified_income": 185000,
            "income_sources": [{"source": "Insurance Reimbursements", "monthly_avg": 142000, "confidence": 0.97}, {"source": "Patient Payments", "monthly_avg": 43000, "confidence": 0.95}],
            "income_stability": "HIGH",
            "months_of_history": 84
        },
        "risk_signals": {
            "nsf_overdraft_count_90d": 0,
            "negative_balance_days_90d": 0,
            "account_age_days": 2520,
            "fraud_signals": [],
            "beacon_network_flags": 0
        }
    }
}

# =============================================================================
# PLAID API SIMULATION FUNCTIONS
# =============================================================================

def plaid_identity_verify(app_data: dict) -> dict:
    """Simulate Plaid Identity + Layer verification"""
    return {
        "verified": True,
        "verification_method": "plaid_layer",
        "identity_match_score": 0.98,
        "business_name_match": True,
        "owner_name_match": True,
        "address_match": True,
        "verification_timestamp": datetime.now().isoformat(),
        "session_id": f"plaid_session_{app_data['business_name'][:3].lower()}_{np.random.randint(10000, 99999)}"
    }

def plaid_get_accounts(app_data: dict) -> dict:
    """Simulate Plaid Accounts endpoint"""
    return {
        "accounts": app_data["linked_accounts"],
        "item_id": f"item_{np.random.randint(100000, 999999)}",
        "request_id": f"req_{np.random.randint(100000, 999999)}"
    }

def plaid_get_transactions(app_data: dict) -> dict:
    """Simulate Plaid Transactions endpoint"""
    return {
        "transactions": app_data["transactions_90d"],
        "total_transactions": len(app_data["transactions_90d"]),
        "request_id": f"req_{np.random.randint(100000, 999999)}"
    }

def plaid_bank_income(app_data: dict) -> dict:
    """Simulate Plaid Bank Income endpoint (ML-verified income)"""
    return {
        "bank_income": app_data["bank_income"],
        "confidence_level": "HIGH" if app_data["bank_income"]["income_stability"] == "HIGH" else "MEDIUM",
        "request_id": f"req_{np.random.randint(100000, 999999)}"
    }

def plaid_signal_score(app_data: dict) -> dict:
    """
    Simulate Plaid Signal - ACH risk scoring
    Uses 1000+ factors from bank data to predict ACH return risk
    """
    risk = app_data["risk_signals"]
    
    # Calculate base score (higher = lower risk, 0-100 scale)
    base_score = 70
    
    # Adjustments based on risk factors
    if risk["nsf_overdraft_count_90d"] == 0:
        base_score += 15
    else:
        base_score -= (risk["nsf_overdraft_count_90d"] * 8)
    
    if risk["negative_balance_days_90d"] == 0:
        base_score += 10
    else:
        base_score -= (risk["negative_balance_days_90d"] * 2)
    
    if risk["account_age_days"] > 365:
        base_score += 5
    if risk["account_age_days"] > 730:
        base_score += 5
    
    base_score = max(0, min(100, base_score))
    
    return {
        "signal_score": round(base_score, 1),
        "risk_tier": "LOW" if base_score >= 75 else ("MEDIUM" if base_score >= 50 else "HIGH"),
        "factors": {
            "nsf_overdraft_history": "GOOD" if risk["nsf_overdraft_count_90d"] == 0 else "CONCERN",
            "balance_stability": "GOOD" if risk["negative_balance_days_90d"] == 0 else "CONCERN",
            "account_tenure": "ESTABLISHED" if risk["account_age_days"] > 365 else "NEW"
        },
        "request_id": f"req_{np.random.randint(100000, 999999)}"
    }

def plaid_beacon_check(app_data: dict) -> dict:
    """
    Simulate Plaid Beacon - Fraud network consortium
    Checks against 8,000+ apps' fraud data
    """
    return {
        "fraud_detected": app_data["risk_signals"]["beacon_network_flags"] > 0,
        "fraud_signals": app_data["risk_signals"]["fraud_signals"],
        "network_alerts": app_data["risk_signals"]["beacon_network_flags"],
        "identity_fraud_risk": "LOW",
        "synthetic_fraud_risk": "LOW",
        "request_id": f"req_{np.random.randint(100000, 999999)}"
    }

def plaid_trust_index(app_data: dict) -> dict:
    """
    Simulate Plaid Trust Index v2 - Graph Neural Network fraud detection
    Uses entity relationships across the Plaid network
    """
    risk = app_data["risk_signals"]
    
    # Higher = more trustworthy (0-1 scale)
    trust_score = 0.85
    
    if risk["beacon_network_flags"] == 0:
        trust_score += 0.08
    else:
        trust_score -= 0.30
    
    if risk["nsf_overdraft_count_90d"] == 0:
        trust_score += 0.05
    else:
        trust_score -= (risk["nsf_overdraft_count_90d"] * 0.08)
    
    if app_data["years_in_business"] >= 2:
        trust_score += 0.02
    
    trust_score = max(0, min(1, trust_score))
    
    return {
        "trust_index": round(trust_score, 3),
        "percentile": int(trust_score * 100),
        "entity_graph_signals": {
            "connected_institutions": len(app_data["linked_accounts"]),
            "account_velocity": "NORMAL",
            "cross_network_risk": "LOW"
        },
        "request_id": f"req_{np.random.randint(100000, 999999)}"
    }

# =============================================================================
# CREDIT ANALYSIS FUNCTIONS
# =============================================================================

def calculate_cash_flow_metrics(app_data: dict) -> dict:
    """Calculate key cash flow metrics from transaction data"""
    txns = app_data["transactions_90d"]
    
    inflows = sum(t["amount"] for t in txns if t["amount"] > 0)
    outflows = abs(sum(t["amount"] for t in txns if t["amount"] < 0))
    
    # Categorize expenses
    payroll = abs(sum(t["amount"] for t in txns if "Payroll" in str(t.get("category", []))))
    rent = abs(sum(t["amount"] for t in txns if "Rent" in str(t.get("category", []))))
    software = abs(sum(t["amount"] for t in txns if "Software" in str(t.get("category", []))))
    
    # Estimate monthly (data is 90 days)
    monthly_inflow = inflows / 3
    monthly_outflow = outflows / 3
    monthly_net = monthly_inflow - monthly_outflow
    
    return {
        "total_inflows_90d": round(inflows, 2),
        "total_outflows_90d": round(outflows, 2),
        "monthly_avg_inflow": round(monthly_inflow, 2),
        "monthly_avg_outflow": round(monthly_outflow, 2),
        "monthly_net_cash_flow": round(monthly_net, 2),
        "payroll_90d": round(payroll, 2),
        "rent_90d": round(rent, 2),
        "operating_margin": round((monthly_net / monthly_inflow * 100) if monthly_inflow > 0 else 0, 1)
    }

def calculate_debt_metrics(app_data: dict, loan_amount: int) -> dict:
    """Calculate debt service coverage ratio and related metrics"""
    bank_income = app_data["bank_income"]["verified_income"]
    cash_flow = calculate_cash_flow_metrics(app_data)
    
    # Get current debt payments (credit card minimums, etc.)
    current_debt = sum(abs(a["balance"]) for a in app_data["linked_accounts"] if a["type"] == "credit")
    credit_limit = sum(a.get("limit", 0) for a in app_data["linked_accounts"] if a["type"] == "credit")
    utilization = (current_debt / credit_limit * 100) if credit_limit > 0 else 0
    
    # Estimate monthly payment on requested loan (simplified: 5-year term, 10% APR)
    monthly_rate = 0.10 / 12
    num_payments = 60
    estimated_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    
    # DSCR = Net Operating Income / Debt Service
    net_income = cash_flow["monthly_net_cash_flow"]
    dscr = net_income / estimated_payment if estimated_payment > 0 else 0
    
    # DTI (Debt-to-Income)
    dti = (estimated_payment / bank_income * 100) if bank_income > 0 else 100
    
    return {
        "dscr": round(dscr, 2),
        "dti_ratio": round(dti, 1),
        "estimated_monthly_payment": round(estimated_payment, 2),
        "current_debt": round(current_debt, 2),
        "credit_utilization": round(utilization, 1),
        "net_operating_income": round(net_income, 2)
    }

def calculate_liquidity_metrics(app_data: dict, loan_amount: int) -> dict:
    """Calculate liquidity and runway metrics"""
    cash_flow = calculate_cash_flow_metrics(app_data)
    
    # Total liquid assets
    liquid_assets = sum(a["balance"] for a in app_data["linked_accounts"] if a["type"] == "depository" and a["balance"] > 0)
    
    # Runway (months of expenses covered by cash)
    monthly_burn = cash_flow["monthly_avg_outflow"]
    runway_months = liquid_assets / monthly_burn if monthly_burn > 0 else 0
    
    # Loan-to-cash ratio
    loan_to_cash = loan_amount / liquid_assets if liquid_assets > 0 else float('inf')
    
    return {
        "liquid_assets": round(liquid_assets, 2),
        "runway_months": round(runway_months, 1),
        "loan_to_cash_ratio": round(loan_to_cash, 2),
        "monthly_burn_rate": round(monthly_burn, 2)
    }

# =============================================================================
# AGENT DECISION ENGINE
# =============================================================================

def agent_make_decision(app_data: dict, plaid_signals: dict, metrics: dict) -> dict:
    """
    AI Agent decision logic for credit approval
    Returns decision with explainable factors
    """
    signal = plaid_signals["signal"]
    beacon = plaid_signals["beacon"]
    trust = plaid_signals["trust"]
    debt = metrics["debt"]
    liquidity = metrics["liquidity"]
    
    # Decision factors
    factors = []
    score = 0
    max_score = 100
    
    # Factor 1: Plaid Signal Score (25 points)
    if signal["signal_score"] >= 80:
        score += 25
        factors.append(("Signal Score", "PASS", f"{signal['signal_score']}/100 - Low ACH return risk"))
    elif signal["signal_score"] >= 60:
        score += 15
        factors.append(("Signal Score", "MARGINAL", f"{signal['signal_score']}/100 - Moderate ACH risk"))
    else:
        score += 5
        factors.append(("Signal Score", "FAIL", f"{signal['signal_score']}/100 - High ACH return risk"))
    
    # Factor 2: Trust Index (20 points)
    if trust["trust_index"] >= 0.90:
        score += 20
        factors.append(("Trust Index", "PASS", f"{trust['trust_index']:.2f} - High network trust"))
    elif trust["trust_index"] >= 0.75:
        score += 12
        factors.append(("Trust Index", "MARGINAL", f"{trust['trust_index']:.2f} - Moderate network trust"))
    else:
        score += 0
        factors.append(("Trust Index", "FAIL", f"{trust['trust_index']:.2f} - Low network trust"))
    
    # Factor 3: Beacon Fraud Check (15 points)
    if not beacon["fraud_detected"]:
        score += 15
        factors.append(("Beacon Fraud", "PASS", "No fraud signals in consortium network"))
    else:
        score += 0
        factors.append(("Beacon Fraud", "FAIL", f"Fraud detected: {beacon['fraud_signals']}"))
    
    # Factor 4: DSCR (20 points)
    if debt["dscr"] >= 1.5:
        score += 20
        factors.append(("DSCR", "PASS", f"{debt['dscr']}x - Strong debt service coverage"))
    elif debt["dscr"] >= 1.2:
        score += 12
        factors.append(("DSCR", "MARGINAL", f"{debt['dscr']}x - Adequate debt service coverage"))
    elif debt["dscr"] >= 1.0:
        score += 6
        factors.append(("DSCR", "MARGINAL", f"{debt['dscr']}x - Minimal debt service coverage"))
    else:
        score += 0
        factors.append(("DSCR", "FAIL", f"{debt['dscr']}x - Insufficient debt service coverage"))
    
    # Factor 5: Liquidity (10 points)
    if liquidity["runway_months"] >= 6:
        score += 10
        factors.append(("Liquidity", "PASS", f"{liquidity['runway_months']} months runway"))
    elif liquidity["runway_months"] >= 3:
        score += 5
        factors.append(("Liquidity", "MARGINAL", f"{liquidity['runway_months']} months runway"))
    else:
        score += 0
        factors.append(("Liquidity", "FAIL", f"{liquidity['runway_months']} months runway - Low cash buffer"))
    
    # Factor 6: Income Verification (10 points)
    income_data = app_data["bank_income"]
    if income_data["income_stability"] == "HIGH" and income_data["months_of_history"] >= 12:
        score += 10
        factors.append(("Income Verification", "PASS", f"Verified ${income_data['verified_income']:,}/mo - High stability"))
    elif income_data["months_of_history"] >= 6:
        score += 5
        factors.append(("Income Verification", "MARGINAL", f"Verified ${income_data['verified_income']:,}/mo - Limited history"))
    else:
        score += 0
        factors.append(("Income Verification", "FAIL", f"Insufficient income history ({income_data['months_of_history']} months)"))
    
    # Make decision
    if beacon["fraud_detected"]:
        decision = "DENIED"
        reason = "Fraud signals detected in Beacon network"
    elif score >= 75:
        decision = "APPROVED"
        reason = f"Strong credit profile (Score: {score}/{max_score})"
    elif score >= 55:
        decision = "MANUAL_REVIEW"
        reason = f"Marginal credit profile requires human review (Score: {score}/{max_score})"
    else:
        decision = "DENIED"
        reason = f"Credit profile does not meet underwriting criteria (Score: {score}/{max_score})"
    
    return {
        "decision": decision,
        "reason": reason,
        "score": score,
        "max_score": max_score,
        "factors": factors,
        "timestamp": datetime.now().isoformat(),
        "audit_id": f"AUD-{datetime.now().strftime('%Y%m%d')}-{np.random.randint(10000, 99999)}"
    }

# =============================================================================
# STREAMLIT UI
# =============================================================================

def main():
    # Sidebar
    with st.sidebar:
        st.markdown("### Plaid Infrastructure")
        st.markdown("""
        **Decision Inputs:**
        
        `Identity + Layer`  
        Applicant verification
        
        `MCP Server`  
        Real-time data queries
        
        `Transactions`  
        90-day cash flow
        
        `Bank Income`  
        ML-verified revenue
        
        `Signal`  
        ACH risk scoring
        
        `Beacon`  
        Fraud consortium
        
        `Trust Index v2`  
        GNN fraud detection
        """)
        
        st.markdown("---")
        
        st.markdown("### Agent Architecture")
        st.code("""
PERCEIVE → REASON → VERIFY → ACT

1. Fetch data (Plaid APIs)
2. Analyze financials (LLM)
3. Check risk (Signal/Beacon)
4. Decision + Audit trail
        """, language=None)
        
        st.markdown("---")
        st.markdown("### Source")
        st.markdown("""
        [PYMNTS Podcast (Aug 2025)](https://www.pymnts.com/podcast/from-infrastructure-to-analytics-the-plaid-playbook/)
        
        *"In an agentic world, the underlying data and the underlying identity source—those are gonna become two of the most crucial elements."*
        
        — Zach Perret, CEO
        """)
    
    # Main content
    st.markdown('<p class="main-header">Credit Decisioning Agent</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Autonomous Credit Decisioning Powered by Plaid Infrastructure</p>', unsafe_allow_html=True)
    
    # Context
    st.markdown("""
    <div class="quote-box">
        <strong>B2B Use Case:</strong> This demonstrates how a lender (fintech, bank, credit union) builds an 
        AI-powered underwriting agent using Plaid's infrastructure. The agent verifies identity, analyzes 
        financial data, assesses risk, and makes credit decisions with full audit trails for compliance.
    </div>
    """, unsafe_allow_html=True)
    
    # Application selector
    st.markdown("### Select Loan Application")
    
    col1, col2, col3 = st.columns(3)
    
    for idx, (app_id, app_data) in enumerate(LOAN_APPLICATIONS.items()):
        with [col1, col2, col3][idx]:
            with st.container(border=True):
                st.markdown(f"**{app_data['business_name']}**")
                st.caption(app_data['business_type'])
                st.markdown(f"### ${app_data['loan_amount']:,}")
                st.caption(app_data['loan_purpose'])
                st.markdown(f"**Plaid linked** | {len(app_data['linked_accounts'])} accounts")
    
    selected_app_id = st.selectbox(
        "Choose application to process:",
        options=list(LOAN_APPLICATIONS.keys()),
        format_func=lambda x: f"{x} | {LOAN_APPLICATIONS[x]['business_name']} | ${LOAN_APPLICATIONS[x]['loan_amount']:,}"
    )
    
    if st.button("Execute Credit Decisioning", type="primary", use_container_width=True):
        app_data = LOAN_APPLICATIONS[selected_app_id]
        
        st.markdown("---")
        st.markdown("### Agent Processing Trace")
        
        # Step 1: Identity Verification
        with st.status("Step 1: Verifying identity via Plaid Layer...", expanded=True) as status:
            time.sleep(0.8)
            identity = plaid_identity_verify(app_data)
            st.markdown(f"""
            <span class="data-source-tag">PLAID LAYER</span>
            <span class="data-source-tag">PLAID IDENTITY</span>
            
            **Business Verified:** {app_data['business_name']}  
            **Owner Verified:** {app_data['owner_name']}  
            **Match Score:** {identity['identity_match_score']}  
            **Session:** `{identity['session_id']}`
            """, unsafe_allow_html=True)
            status.update(label="Step 1: Identity Verified ✓", state="complete")
        
        # Step 2: Fetch Financial Data
        with st.status("Step 2: Fetching financial data via MCP Server...", expanded=True) as status:
            time.sleep(1.0)
            accounts = plaid_get_accounts(app_data)
            transactions = plaid_get_transactions(app_data)
            bank_income = plaid_bank_income(app_data)
            
            st.markdown(f"""
            <span class="data-source-tag">PLAID MCP SERVER</span>
            <span class="data-source-tag">TRANSACTIONS</span>
            <span class="data-source-tag">BANK INCOME</span>
            """, unsafe_allow_html=True)
            
            # Show accounts
            st.markdown("**Linked Accounts:**")
            acc_df = pd.DataFrame(accounts["accounts"])
            acc_df["balance"] = acc_df["balance"].apply(lambda x: f"${x:,.2f}")
            st.dataframe(acc_df[["institution", "name", "type", "balance"]], use_container_width=True, hide_index=True)
            
            st.markdown(f"""
            **Bank Income (ML-Verified):** ${bank_income['bank_income']['verified_income']:,}/month  
            **Income Stability:** {bank_income['bank_income']['income_stability']}  
            **History:** {bank_income['bank_income']['months_of_history']} months
            """)
            status.update(label="Step 2: Financial Data Retrieved ✓", state="complete")
        
        # Step 3: Calculate Metrics
        with st.status("Step 3: Analyzing cash flow and credit metrics...", expanded=True) as status:
            time.sleep(0.8)
            cash_flow = calculate_cash_flow_metrics(app_data)
            debt_metrics = calculate_debt_metrics(app_data, app_data["loan_amount"])
            liquidity_metrics = calculate_liquidity_metrics(app_data, app_data["loan_amount"])
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Monthly Revenue", f"${cash_flow['monthly_avg_inflow']:,.0f}")
            col2.metric("DSCR", f"{debt_metrics['dscr']}x")
            col3.metric("DTI Ratio", f"{debt_metrics['dti_ratio']}%")
            col4.metric("Cash Runway", f"{liquidity_metrics['runway_months']} mo")
            
            status.update(label="Step 3: Credit Metrics Calculated ✓", state="complete")
        
        # Step 4: Risk Assessment
        with st.status("Step 4: Assessing risk via Signal + Beacon + Trust Index...", expanded=True) as status:
            time.sleep(1.2)
            signal = plaid_signal_score(app_data)
            beacon = plaid_beacon_check(app_data)
            trust = plaid_trust_index(app_data)
            
            st.markdown(f"""
            <span class="data-source-tag">PLAID SIGNAL</span>
            <span class="data-source-tag">PLAID BEACON</span>
            <span class="data-source-tag">TRUST INDEX V2</span>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=signal["signal_score"],
                    title={'text': "<span style='color:#14B8A6'>Signal Score</span>"},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "#14B8A6"},
                        'steps': [
                            {'range': [0, 50], 'color': "#FEE2E2"},
                            {'range': [50, 75], 'color': "#FEF3C7"},
                            {'range': [75, 100], 'color': "#D1FAE5"}
                        ]
                    }
                ))
                fig.update_layout(height=200, margin=dict(t=80, b=0, l=30, r=30))
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=trust["trust_index"],
                    title={'text': "Trust Index"},
                    gauge={
                        'axis': {'range': [0, 1]},
                        'bar': {'color': "#0055FF"},
                        'steps': [
                            {'range': [0, 0.5], 'color': "#FEE2E2"},
                            {'range': [0.5, 0.8], 'color': "#FEF3C7"},
                            {'range': [0.8, 1], 'color': "#D1FAE5"}
                        ]
                    }
                ))
                fig.update_layout(height=200, margin=dict(t=80, b=0, l=30, r=30))
                st.plotly_chart(fig, use_container_width=True)
            
            with col3:
                fraud_status = "CLEAR" if not beacon["fraud_detected"] else "FLAGGED"
                color = "#16A34A" if not beacon["fraud_detected"] else "#DC2626"
                st.markdown(f"""
                <div style="text-align: center; padding-top: 40px;">
                    <p style="font-size: 0.9rem; color: #64748B;">Beacon Fraud Check</p>
                    <p style="font-size: 1.8rem; font-weight: 700; color: {color};">{fraud_status}</p>
                    <p style="font-size: 0.8rem; color: #64748B;">Network Alerts: {beacon['network_alerts']}</p>
                </div>
                """, unsafe_allow_html=True)
            
            status.update(label="Step 4: Risk Assessment Complete ✓", state="complete")
        
        # Step 5: Decision
        with st.status("Step 5: Making credit decision...", expanded=True) as status:
            time.sleep(0.6)
            
            plaid_signals = {"signal": signal, "beacon": beacon, "trust": trust}
            metrics = {"debt": debt_metrics, "liquidity": liquidity_metrics}
            
            decision = agent_make_decision(app_data, plaid_signals, metrics)
            
            status.update(label="Step 5: Decision Rendered ✓", state="complete")
        
        # Display Decision
        st.markdown("---")
        st.markdown("### Credit Decision")
        st.caption("Decision reflects real-time identity, cash flow, and network risk signals")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            decision_class = {
                "APPROVED": "decision-approved",
                "DENIED": "decision-denied",
                "MANUAL_REVIEW": "decision-review"
            }[decision["decision"]]
            
            st.markdown(f"""
            <div class="{decision_class}">
                {decision["decision"].replace("_", " ")}
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            **Score:** {decision['score']}/{decision['max_score']}  
            **Audit ID:** `{decision['audit_id']}`
            """)
        
        with col2:
            st.markdown(f"**Applicant:** {app_data['business_name']}")
            st.markdown(f"**Loan Amount:** ${app_data['loan_amount']:,}")
            st.markdown(f"**Decision Reason:** {decision['reason']}")
            st.markdown(f"**Timestamp:** {decision['timestamp']}")
        
        # Decision Factors
        st.markdown("### Decision Factors (Explainability)")
        
        factors_df = pd.DataFrame(decision["factors"], columns=["Factor", "Result", "Details"])
        
        def color_result(val):
            if val == "PASS":
                return "background-color: #D1FAE5; color: #065F46"
            elif val == "FAIL":
                return "background-color: #FEE2E2; color: #991B1B"
            else:
                return "background-color: #FEF3C7; color: #92400E"
        
        st.dataframe(
            factors_df.style.applymap(color_result, subset=["Result"]),
            use_container_width=True,
            hide_index=True
        )
        
        # Audit Trail
        with st.expander("Full Audit Trail (Compliance)"):
            audit_data = {
                "audit_id": decision["audit_id"],
                "timestamp": decision["timestamp"],
                "application_id": selected_app_id,
                "applicant": app_data["business_name"],
                "loan_amount": app_data["loan_amount"],
                "loan_purpose": app_data["loan_purpose"],
                "decision": decision["decision"],
                "decision_reason": decision["reason"],
                "decision_score": f"{decision['score']}/{decision['max_score']}",
                "plaid_data_sources": [
                    "plaid_layer",
                    "plaid_identity",
                    "plaid_mcp_server",
                    "plaid_transactions",
                    "plaid_bank_income",
                    "plaid_signal",
                    "plaid_beacon",
                    "plaid_trust_index_v2"
                ],
                "risk_scores": {
                    "signal_score": signal["signal_score"],
                    "trust_index": trust["trust_index"],
                    "beacon_fraud_detected": beacon["fraud_detected"]
                },
                "credit_metrics": {
                    "dscr": debt_metrics["dscr"],
                    "dti_ratio": debt_metrics["dti_ratio"],
                    "runway_months": liquidity_metrics["runway_months"]
                },
                "decision_factors": decision["factors"],
                "agent_version": "credit-agent-v1.0",
                "model_id": "plaid-underwriting-2025"
            }
            st.json(audit_data)

        with st.expander("Product Rationale: Real-Time Data in Credit Decisions"):
            st.markdown("""
                **Context**
                Traditional credit scores are slow to reflect changes in a user’s financial situation and provide limited signal at the moment a decision is made.
            
                **Observed Gap**
                Static scores underperform for users with volatile income, thin credit files, or recent financial recovery, leading to delayed approvals and avoidable risk.
            
                **Design Choice**
                This agent uses real-time, permissioned financial data to evaluate cash flow health, account behavior, and cross-app signals at decision time.
            
                **Expected Impact**
                Prioritizing current financial context improves approval precision while reducing downstream fraud and repayment risk.
            """)


if __name__ == "__main__":
    main()
