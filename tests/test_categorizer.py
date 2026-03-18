import sys
import os

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend'))
sys.path.insert(0, backend_path)

from categorizer import categorize


# --- Income ---

def test_upi_credit_is_income():
    assert categorize("UPI/CR/564601090524/Bharati/YESB/paytm.d128/expre") == "Income"

def test_neft_transfer_is_income():
    assert categorize("NEFT*HDFC0000240*HDFCH00524301404*SHIVAM ASSOCIATE") == "Income"


# --- Reversal ---

def test_upi_reversal_is_reversal():
    assert categorize("UPI/REV/564895272357") == "Reversal"


# --- Transport ---

def test_petro_is_transport():
    assert categorize("UPI/DR/527443106726/ANURADHA/YESB/q907299546/petro") == "Transport"

def test_fuel_is_transport():
    assert categorize("UPI/DR/123456789012/HP FUEL STATION/YESB/UPI") == "Transport"


# --- Food ---

def test_zomato_is_food():
    assert categorize("UPI/DR/123456789012/ZOMATO/YESB/zomato123/UPI") == "Food"

def test_swiggy_is_food():
    assert categorize("UPI/DR/123456789012/SWIGGY ORDER/YESB/UPI") == "Food"


# --- Groceries ---

def test_mart_is_groceries():
    assert categorize("UPI/DR/527798397659/AMART/YESB/q475396944/UPI") == "Groceries"

def test_dmart_is_groceries():
    assert categorize("UPI/DR/123456789012/DMART STORE/YESB/UPI") == "Groceries"


# --- Utilities ---

def test_contr_is_utilities():
    assert categorize("UPI/DR/564531315696/MANTHAN/IPOS/tatkarmant/contr") == "Utilities"

def test_electric_is_utilities():
    assert categorize("UPI/DR/123456789012/MSEB ELECTRIC BILL/YESB/UPI") == "Utilities"


# --- Transfer (generic UPI debit that matches no specific category) ---

def test_generic_upi_debit_is_transfer():
    assert categorize("UPI/DR/527441355320/ANNAPURN/YESB/q027322192/UPI") == "Transfer"

def test_transfer_to_is_transfer():
    assert categorize("TRANSFER TO 4897693162093") == "Transfer"


# --- Fallback ---

def test_unrecognised_description_returns_other():
    assert categorize("SOME COMPLETELY UNKNOWN TRANSACTION STRING") == "Other"


# --- Case insensitivity ---

def test_matching_is_case_insensitive():
    assert categorize("UPI/DR/123456/ZOMATO FOODS/YESB/UPI") == "Food"
    assert categorize("upi/cr/123456/someone/yesb/upi") == "Income"


# --- Rule ordering: Income and Reversal must beat Transfer ---

def test_credit_is_not_classified_as_transfer():
    result = categorize("UPI/CR/564601090524/Bharati/YESB/paytm.d128")
    assert result == "Income"
    assert result != "Transfer"

def test_reversal_is_not_classified_as_transfer():
    result = categorize("UPI/REV/564895272357")
    assert result == "Reversal"
    assert result != "Transfer"