import re
from typing import Dict, List, Set, Tuple, Callable
from faker import Faker
from db_utils import insert_data, get_db_connection

def mask_digits(text: str) -> str:
    return re.sub(r'\d', '#', text)

def get_state(fake: Faker) -> str:
    return fake.state() if hasattr(fake, 'state') else fake.administrative_unit()

def generate_unique(generator_func: Callable, count: int) -> Set:
    results = set()
    while len(results) < count:
        results.add(generator_func())
    return results

def gen_locales(locales_config: Dict[str, str]) -> List[Tuple]:
    return [(loc, country) for loc, country in locales_config.items()]

def gen_first_names(fakers: Dict[str, Faker], rows: int) -> List[Tuple]:
    data = []
    for loc, fake in fakers.items():
        males = [(loc, name, 'M') for name in generate_unique(fake.first_name_male, rows // 2)]
        females = [(loc, name, 'F') for name in generate_unique(fake.first_name_female, rows // 2)]
        data.extend(males + females)
    return data

def gen_last_names(fakers: Dict[str, Faker], rows: int) -> List[Tuple]:
    data = []
    for loc, fake in fakers.items():
        data.extend([(loc, name) for name in generate_unique(fake.last_name, rows)])
    return data

def gen_titles(fakers: Dict[str, Faker], count: int = 20) -> List[Tuple]:
    data = []
    for loc, fake in fakers.items():
        males = [(loc, prefix, 'M') for prefix in generate_unique(fake.prefix_male, count)]
        females = [(loc, prefix, 'F') for prefix in generate_unique(fake.prefix_female, count)]
        data.extend(males + females)
    return data

def gen_streets(fakers: Dict[str, Faker], rows: int) -> List[Tuple]:
    data = []
    for loc, fake in fakers.items():
        data.extend([(loc, street) for street in generate_unique(fake.street_name, rows)])
    return data

def gen_cities(fakers: Dict[str, Faker], rows: int) -> List[Tuple]:
    data = []
    for loc, fake in fakers.items():
        unique_cities = set()
        while len(unique_cities) < (rows // 2):
            unique_cities.add((loc, fake.city(), get_state(fake), mask_digits(fake.postcode())))
        data.extend(list(unique_cities))
    return data

def gen_email_domains(fakers: Dict[str, Faker], count: int = 50) -> List[Tuple]:
    data = []
    for loc, fake in fakers.items():
        data.extend([(loc, domain) for domain in generate_unique(fake.free_email_domain, count)])
    return data

def gen_phone_formats(fakers: Dict[str, Faker], count: int = 200) -> List[Tuple]:
    data = []
    for loc, fake in fakers.items():
        formats = set()
        while len(formats) < count:
            formats.add((loc, mask_digits(fake.phone_number())))
        data.extend(list(formats))
    return data

def get_discrete_attributes(locales: List[str]) -> Tuple[List[Tuple], List[Tuple]]:
    discrete_data = {
        'en_US': {
            'eye': ['Blue', 'Brown', 'Green', 'Hazel', 'Gray', 'Amber'],
            'hair': ['Black', 'Brown', 'Blonde', 'Red', 'Gray', 'White']
        },
        'pl_PL': {
            'eye': ['Niebieski', 'Brązowy', 'Zielony', 'Czarny', 'Szary', 'Piwny'],
            'hair': ['Czarny', 'Brązowy', 'Blond', 'Rudy', 'Szary', 'Biały']
        }
    }
    eye_data, hair_data = [], []
    for loc in locales:
        dict_loc = loc if loc in discrete_data else 'en_US'
        eye_data.extend([(loc, color) for color in discrete_data[dict_loc]['eye']])
        hair_data.extend([(loc, color) for color in discrete_data[dict_loc]['hair']])
    return eye_data, hair_data

class LookupFiller:
    def __init__(self, connection, locales_config: Dict[str, str], rows: int = 5000):
        self.connection = connection
        self.locales_config = locales_config
        self.rows = rows
        self.fakers = {locale: Faker(locale) for locale in locales_config.keys()}

    def populate_lookups(self):
        tasks = [
            ("locales", "locale_code, country_name", gen_locales(self.locales_config)),
            ("lookup_email_domains", "locale_code, domain_name", gen_email_domains(self.fakers)),
            ("lookup_titles", "locale_code, title_text, gender", gen_titles(self.fakers)),
            ("lookup_phone_formats", "locale_code, format_pattern", gen_phone_formats(self.fakers)),
            ("lookup_first_names", "locale_code, first_name, gender", gen_first_names(self.fakers, self.rows)),
            ("lookup_last_names", "locale_code, last_name", gen_last_names(self.fakers, self.rows)),
            ("lookup_streets", "locale_code, street_name", gen_streets(self.fakers, self.rows)),
            ("lookup_cities", "locale_code, city_name, state_or_region, postal_code_pattern", gen_cities(self.fakers, self.rows)),
        ]

        for table, columns, data in tasks:
            conflict = " ON CONFLICT DO NOTHING" if table == "locales" else ""
            insert_data(self.connection, f"INSERT INTO {table} ({columns}) VALUES %s{conflict};", data)

        eye_data, hair_data = get_discrete_attributes(list(self.locales_config.keys()))
        insert_data(self.connection, "INSERT INTO lookup_eye_colors (locale_code, color_name) VALUES %s;", eye_data)
        insert_data(self.connection, "INSERT INTO lookup_hair_colors (locale_code, color_name) VALUES %s;", hair_data)

if __name__ == "__main__":
    SUPPORTED_LOCALES = {
        'en_US': 'United States',
        'pl_PL': 'Poland'
    }
    
    connection = get_db_connection()
    try:
        filler = LookupFiller(connection, locales_config=SUPPORTED_LOCALES, rows=5)
        filler.populate_lookups()
    except Exception as e:
        print(f"Error occurred: {e}")
        connection.rollback()
    finally:
        if connection:
            connection.close()
