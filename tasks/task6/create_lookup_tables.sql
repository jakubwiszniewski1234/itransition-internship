
CREATE TABLE locales (
    locale_code VARCHAR(10) PRIMARY KEY,
    country_name VARCHAR(100) NOT NULL
);

CREATE TABLE lookup_first_names (
    id INT IDENTITY(1,1) PRIMARY KEY,
    locale_code VARCHAR(10) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    gender CHAR(1) NOT NULL
);

CREATE TABLE lookup_last_names (
    id INT IDENTITY(1,1) PRIMARY KEY,
    locale_code VARCHAR(10) NOT NULL,
    last_name VARCHAR(100) NOT NULL
);

CREATE TABLE lookup_titles (
    id INT IDENTITY(1,1) PRIMARY KEY,
    locale_code VARCHAR(10) NOT NULL,
    title_text VARCHAR(20) NOT NULL,
    gender CHAR(1) NULL
);

CREATE TABLE lookup_streets (
    id INT IDENTITY(1,1) PRIMARY KEY,
    locale_code VARCHAR(10) NOT NULL,
    street_name VARCHAR(100) NOT NULL
);

CREATE TABLE lookup_cities (
    id INT IDENTITY(1,1) PRIMARY KEY,
    locale_code VARCHAR(10) NOT NULL,
    city_name VARCHAR(100) NOT NULL,
    state_or_region VARCHAR(100) NOT NULL,
    postal_code_pattern VARCHAR(20) NOT NULL
);

CREATE TABLE lookup_email_domains (
    id INT IDENTITY(1,1) PRIMARY KEY,
    locale_code VARCHAR(10) NOT NULL,
    domain_name VARCHAR(100) NOT NULL
);

CREATE TABLE lookup_phone_formats (
    id INT IDENTITY(1,1) PRIMARY KEY,
    locale_code VARCHAR(10) NOT NULL,
    format_pattern VARCHAR(50) NOT NULL
);

CREATE TABLE lookup_eye_colors (
    id INT IDENTITY(1,1) PRIMARY KEY,
    locale_code VARCHAR(10) NOT NULL,
    color_name VARCHAR(30) NOT NULL
);

CREATE TABLE lookup_hair_colors (
    id INT IDENTITY(1,1) PRIMARY KEY,
    locale_code VARCHAR(10) NOT NULL,
    color_name VARCHAR(30) NOT NULL
);

CREATE INDEX idx_lookup_first_names_locale_id ON lookup_first_names (locale_code, id);
CREATE INDEX idx_lookup_last_names_locale_id ON lookup_last_names (locale_code, id);
CREATE INDEX idx_lookup_titles_locale_id ON lookup_titles (locale_code, id);
CREATE INDEX idx_lookup_streets_locale_id ON lookup_streets (locale_code, id);
CREATE INDEX idx_lookup_cities_locale_id ON lookup_cities (locale_code, id);