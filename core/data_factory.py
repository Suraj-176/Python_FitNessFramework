from faker import Faker
import random
import string
import uuid
from datetime import datetime

class DataFactory:
    """Generate realistic test data using Faker library"""
    
    def __init__(self, locale='en_US'):
        self.fake = Faker(locale)
    
    # Person Data
    def generate_first_name(self) -> str:
        return self.fake.first_name()
    
    def generate_last_name(self) -> str:
        return self.fake.last_name()
    
    def generate_full_name(self) -> str:
        return self.fake.name()
    
    def generate_email(self) -> str:
        return self.fake.email()
    
    def generate_phone(self) -> str:
        return self.fake.phone_number()
    
    def generate_ssn(self) -> str:
        return self.fake.ssn()
        
    def generate_username(self) -> str:
        return self.fake.user_name()
        
    def generate_date_of_birth(self) -> str:
        return self.fake.date_of_birth(minimum_age=18, maximum_age=90).isoformat()
    
    # Address Data
    def generate_street_address(self) -> str:
        return self.fake.street_address()
    
    def generate_city(self) -> str:
        return self.fake.city()
    
    def generate_state(self) -> str:
        return self.fake.state()
    
    def generate_zipcode(self) -> str:
        return self.fake.zipcode()
    
    def generate_country(self) -> str:
        return self.fake.country()
    
    def generate_address(self) -> dict:
        return {
            "street": self.generate_street_address(),
            "city": self.generate_city(),
            "state": self.generate_state(),
            "zipcode": self.generate_zipcode(),
            "country": self.generate_country()
        }
    
    # Financial Data
    def generate_credit_card(self) -> str:
        return self.fake.credit_card_number()
    
    def generate_credit_card_expiry(self) -> str:
        return self.fake.credit_card_expire()
    
    def generate_cvv(self) -> str:
        return str(random.randint(100, 999))
    
    def generate_iban(self) -> str:
        return self.fake.iban()
    
    def generate_currency_code(self) -> str:
        return random.choice(['USD', 'EUR', 'GBP', 'INR', 'JPY'])
    
    # Complex Data
    def generate_user_profile(self) -> dict:
        return {
            "id": self.generate_uuid(),
            "username": self.generate_username(),
            "email": self.generate_email(),
            "first_name": self.generate_first_name(),
            "last_name": self.generate_last_name(),
            "phone": self.generate_phone(),
            "address": self.generate_address(),
            "date_of_birth": self.generate_date_of_birth(),
            "created_at": self.generate_timestamp()
        }
    
    def generate_transaction(self) -> dict:
        return {
            "transaction_id": self.generate_uuid(),
            "amount": round(random.uniform(10.0, 10000.0), 2),
            "currency": self.generate_currency_code(),
            "timestamp": self.generate_timestamp(),
            "status": random.choice(['pending', 'completed', 'failed']),
            "payment_method": random.choice(['credit_card', 'debit_card', 'paypal', 'bank_transfer'])
        }
    
    # Utility Methods
    def generate_uuid(self) -> str:
        return str(uuid.uuid4())
    
    def generate_alphanumeric(self, length: int = 10) -> str:
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def generate_timestamp(self) -> str:
        return datetime.now().isoformat()

# Singleton instance
_data_factory_instance = None

def get_data_factory() -> DataFactory:
    """Get singleton instance of DataFactory"""
    global _data_factory_instance
    if _data_factory_instance is None:
        _data_factory_instance = DataFactory()
    return _data_factory_instance
