import pytest
from core.data_factory import get_data_factory, DataFactory

class TestDataFactory:
    """Test test data factory generation logic"""
    
    def test_singleton_instance(self):
        """get_data_factory should always return the same singleton instance"""
        f1 = get_data_factory()
        f2 = get_data_factory()
        assert f1 is f2
        assert isinstance(f1, DataFactory)
        
    def test_generate_name_and_contact(self):
        """Should generate realistic first, last, full names, email, and phone"""
        factory = get_data_factory()
        
        first = factory.generate_first_name()
        last = factory.generate_last_name()
        full = factory.generate_full_name()
        email = factory.generate_email()
        phone = factory.generate_phone()
        ssn = factory.generate_ssn()
        username = factory.generate_username()
        dob = factory.generate_date_of_birth()
        
        assert len(first) > 0
        assert len(last) > 0
        assert len(full) > 0
        assert "@" in email
        assert len(phone) > 0
        assert len(ssn) > 0
        assert len(username) > 0
        assert len(dob) == 10  # YYYY-MM-DD
        
    def test_generate_address(self):
        """Should generate structured address dictionary"""
        factory = get_data_factory()
        addr = factory.generate_address()
        
        assert isinstance(addr, dict)
        assert "street" in addr
        assert "city" in addr
        assert "state" in addr
        assert "zipcode" in addr
        assert "country" in addr
        
    def test_generate_financial(self):
        """Should generate credit card, iban, and currency details"""
        factory = get_data_factory()
        cc = factory.generate_credit_card()
        iban = factory.generate_iban()
        curr = factory.generate_currency_code()
        cvv = factory.generate_cvv()
        
        assert len(cc) >= 13
        assert len(iban) > 0
        assert curr in ['USD', 'EUR', 'GBP', 'INR', 'JPY']
        assert len(cvv) == 3
        
    def test_generate_complex_types(self):
        """Should generate complete user profiles and transactions"""
        factory = get_data_factory()
        profile = factory.generate_user_profile()
        tx = factory.generate_transaction()
        
        assert isinstance(profile, dict)
        assert "id" in profile
        assert "username" in profile
        assert "email" in profile
        
        assert isinstance(tx, dict)
        assert "transaction_id" in tx
        assert tx["amount"] > 0
        assert tx["status"] in ['pending', 'completed', 'failed']
