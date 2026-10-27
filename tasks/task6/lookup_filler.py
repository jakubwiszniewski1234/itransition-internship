import os
import re
from typing import Dict, List, Set, Tuple
import psycopg2
from psycopg2.extras import execute_values
from faker import Faker

def read_env(name:str):
    return os.getenv(f"DB_{name.upper()}")

def get_db_credentials():
    credentials = ["host", "port", "name", "user", "password"]
    return {cred: read_env(cred) for cred in credentials}

def get_db_connection():
    return psycopg2.connect(**get_db_credentials())

class LookupFiller:
    DEFAULT_LOCALE = "en_US"

    def __init__(self, connection, locales_config: Dict[str, str], rows: int = 5000):
        self.connection = connection
        self.locales_config = locales_config
        self.rows = rows
        self.fakers = {locale: Faker(locale) for locale in locales_config.keys()}

        self.discrete_data = {
            'en_US': {
                'eye_colors': ['Blue', 'Brown', 'Green', 'Hazel', 'Gray', 'Amber'],
                'hair_colors': ['Black', 'Brown', 'Blonde', 'Red', 'Gray', 'White']
            },
            'pl_PL': {
                'eye_colors': ['Niebieski', 'Brązowy', 'Zielony', 'Czarny', 'Szary', 'Piwny'],
                'hair_colors': ['Czarny', 'Brązowy', 'Blond', 'Rudy', 'Szary', 'Biały']
            }
        }

    def _insert(self, query: str, data: List[Tuple]):
        if not data:
            return
        with self.connection.cursor() as cursor:
            execute_values(cursor, query, data)
        self.connection.commit()

    def fill_locales(self):
        data = [(loc, country) for loc, country in self.locales_config.items()]
        query = "INSERT INTO locales (locale_code, country_name) VALUES %s ON CONFLICT DO NOTHING;"
        self._insert(query, data)

    def fill_first_names(self):
        print("\n--- Populating lookup_first_names ---")
        data = []
        for loc, fake in self.fakers.items():
            unique_names = set()
            # Generate Male names
            while len(unique_names) < (self.rows // 2):
                unique_names.add((loc, fake.first_name_male(), 'M'))
            # Generate Female names
            female_start_len = len(unique_names)
            while len(unique_names) < female_start_len + (self.rows // 2):
                unique_names.add((loc, fake.first_name_female(), 'F'))
            data.extend(list(unique_names))
            
        query = "INSERT INTO lookup_first_names (locale_code, first_name, gender) VALUES %s;"
        self._insert(query, data)

    def fill_last_names(self):
        print("\n--- Populating lookup_last_names ---")
        data = []
        for loc, fake in self.fakers.items():
            unique_names = set()
            while len(unique_names) < self.rows:
                unique_names.add((loc, fake.last_name()))
            data.extend(list(unique_names))
            
        query = "INSERT INTO lookup_last_names (locale_code, last_name) VALUES %s;"
        self._insert(query, data)

    def fill_titles(self):
        print("\n--- Populating lookup_titles ---")
        data = []
        for loc, fake in self.fakers.items():
            titles = set()
            for _ in range(20):
                titles.add((loc, fake.prefix_male(), 'M'))
                titles.add((loc, fake.prefix_female(), 'F'))
            data.extend(list(titles))
            
        query = "INSERT INTO lookup_titles (locale_code, title_text, gender) VALUES %s;"
        self._insert(query, data)

    def fill_streets(self):
        print("\n--- Populating lookup_streets ---")
        data = []
        for loc, fake in self.fakers.items():
            streets = set()
            while len(streets) < self.rows:
                streets.add((loc, fake.street_name()))
            data.extend(list(streets))
            
        query = "INSERT INTO lookup_streets (locale_code, street_name) VALUES %s;"
        self._insert(query, data)

    def fill_cities(self):
        print("\n--- Populating lookup_cities ---")
        data = []
        for loc, fake in self.fakers.items():
            cities = set()
            while len(cities) < (self.rows // 2): # Slightly fewer cities than names
                state = fake.state() if hasattr(fake, 'state') else fake.administrative_unit()
                # Create a postal pattern by replacing digits with '#'
                postcode = fake.postcode()
                pattern = re.sub(r'\d', '#', postcode)
                
                cities.add((loc, fake.city(), state, pattern))
            data.extend(list(cities))
            
        query = "INSERT INTO lookup_cities (locale_code, city_name, state_or_region, postal_code_pattern) VALUES %s;"
        self._insert(query, data)

    def fill_email_domains(self):
        print("\n--- Populating lookup_email_domains ---")
        data = []
        for loc, fake in self.fakers.items():
            domains = set()
            for _ in range(50):
                domains.add((loc, fake.free_email_domain()))
            data.extend(list(domains))
            
        query = "INSERT INTO lookup_email_domains (locale_code, domain_name) VALUES %s;"
        self._insert(query, data)

    def fill_phone_formats(self):
        print("\n--- Populating lookup_phone_formats ---")
        data = []
        for loc, fake in self.fakers.items():
            formats = set()
            for _ in range(200):
                # Replace all numbers in a fake phone number with '#' to generate the pattern
                phone = fake.phone_number()
                pattern = re.sub(r'\d', '#', phone)
                formats.add((loc, pattern))
            data.extend(list(formats))
            
        query = "INSERT INTO lookup_phone_formats (locale_code, format_pattern) VALUES %s;"
        self._insert(query, data)

    def fill_discrete_attributes(self):
        print("\n--- Populating eye and hair colors ---")
        eye_data = []
        hair_data = []
        
        for loc in self.locales_config.keys():
            dict_loc = loc if loc in self.discrete_data else LookupFiller.DEFAULT_LOCALE

            for color in self.discrete_data[dict_loc]['eye_colors']:
                eye_data.append((loc, color))
            for color in self.discrete_data[dict_loc]['hair_colors']:
                hair_data.append((loc, color))
                
        self._insert("INSERT INTO lookup_eye_colors (locale_code, color_name) VALUES %s;", eye_data)
        self._insert("INSERT INTO lookup_hair_colors (locale_code, color_name) VALUES %s;", hair_data)

    def fill(self):
        try:
            self.fill_locales()
            self.fill_discrete_attributes()
            self.fill_email_domains()
            self.fill_titles()
            self.fill_phone_formats()
            self.fill_first_names()
            self.fill_last_names()
            self.fill_streets()
            self.fill_cities()
        except Exception as e:
            self.connection.rollback()

if __name__ == "__main__":
    # Configuration
    SUPPORTED_LOCALES = {
        'en_US': 'United States',
        'pl_PL': 'Poland'
    }
    
    # 1. Connect
    connection = get_db_connection()
    
    try:
        filler = LookupFiller(connection, locales_config=SUPPORTED_LOCALES, rows=2000)
        filler.fill()
    finally:
        if connection:
            connection.close()