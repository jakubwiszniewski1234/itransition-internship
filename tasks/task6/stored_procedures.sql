DROP ROUTINE IF EXISTS generate_users_batch(BIGINT, VARCHAR, INT, INT);
DROP ROUTINE IF EXISTS generate_full_name(BIGINT, VARCHAR, INT, INT, TEXT[], TEXT[], TEXT[]);
DROP ROUTINE IF EXISTS generate_address(BIGINT, VARCHAR, INT, INT, TEXT[], TEXT[], TEXT[], TEXT[]);
DROP ROUTINE IF EXISTS generate_geolocation(BIGINT, VARCHAR, INT, INT);
DROP ROUTINE IF EXISTS generate_physical_attributes(BIGINT, VARCHAR, INT, INT, TEXT[]);
DROP ROUTINE IF EXISTS generate_physical_attributes(BIGINT, VARCHAR, INT, INT, TEXT[], TEXT[]);
DROP ROUTINE IF EXISTS generate_phone(BIGINT, VARCHAR, INT, INT, TEXT[]);
DROP ROUTINE IF EXISTS generate_email(BIGINT, VARCHAR, INT, INT, INT, TEXT[], TEXT);
DROP ROUTINE IF EXISTS rnorm(BIGINT, VARCHAR, INT, INT, INT, DOUBLE PRECISION, DOUBLE PRECISION);
DROP ROUTINE IF EXISTS rng(BIGINT, VARCHAR, INT, INT, INT);

DROP TABLE IF EXISTS users;

CREATE OR REPLACE FUNCTION rng(
    seed BIGINT,
    locale VARCHAR(10),
    batch_index INT,
    row_index INT,
    identifier INT
) RETURNS DOUBLE PRECISION
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN (hashtext(seed::TEXT || '_' || 
        locale || '_' || 
        batch_index::TEXT || '_' || 
        row_index::TEXT || '_' || 
        identifier::TEXT
    ) & 2147483647) / 2147483647.0;
END;
$$;

CREATE OR REPLACE PROCEDURE rnorm(
    IN seed BIGINT,
    IN locale VARCHAR(10),
    IN batch_index INT,
    IN row_index INT,
    IN identifier INT,
    IN mean DOUBLE PRECISION,
    IN std DOUBLE PRECISION,
    OUT out_random_normal DOUBLE PRECISION
)
LANGUAGE plpgsql
AS $$
DECLARE
    u1 DOUBLE PRECISION;
    u2 DOUBLE PRECISION;
    z DOUBLE PRECISION;
BEGIN
    u1 := rng(seed, locale, batch_index, row_index, identifier);
    u2 := rng(seed, locale, batch_index, row_index, identifier + 1);
    z := sqrt(-2.0 * ln(u1)) * cos(2.0 * pi() * u2);
    out_random_normal := mean + (std * z);
END;
$$;

CREATE OR REPLACE PROCEDURE generate_full_name(
    IN seed BIGINT, IN locale VARCHAR(10), IN batch_index INT, IN row_index INT,
    IN arr_titles TEXT[], IN arr_fn TEXT[], IN arr_ln TEXT[],
    OUT full_name TEXT
) LANGUAGE plpgsql AS $$
DECLARE
    u DOUBLE PRECISION; u1 DOUBLE PRECISION; u2 DOUBLE PRECISION;
    title TEXT := ''; 
    chosen_first_name TEXT := ''; chosen_middle_name TEXT := ''; chosen_last_name TEXT := '';
BEGIN
    u1 := rng(seed, locale, batch_index, row_index, 1);
    IF u1 < 0.05 AND arr_titles IS NOT NULL THEN
        u2 := rng(seed, locale, batch_index, row_index, 2);
        title := arr_titles[ LEAST(1 + floor(u2 * array_length(arr_titles, 1))::INT, array_length(arr_titles, 1)) ];
    END IF;

    u := rng(seed, locale, batch_index, row_index, 3);
    chosen_first_name := arr_fn[ LEAST(1 + floor(u * array_length(arr_fn, 1))::INT, array_length(arr_fn, 1)) ];

    u1 := rng(seed, locale, batch_index, row_index, 4);
    IF u1 < 0.05 AND arr_fn IS NOT NULL THEN
        u2 := rng(seed, locale, batch_index, row_index, 5);
        chosen_middle_name := arr_fn[ LEAST(1 + floor(u2 * array_length(arr_fn, 1))::INT, array_length(arr_fn, 1)) ];
    END IF;

    u := rng(seed, locale, batch_index, row_index, 6);
    chosen_last_name := arr_ln[ LEAST(1 + floor(u * array_length(arr_ln, 1))::INT, array_length(arr_ln, 1)) ];

    full_name := TRIM(
        CASE WHEN title <> '' THEN title || ' ' ELSE '' END ||
        chosen_first_name ||
        CASE WHEN chosen_middle_name <> '' THEN ' ' || chosen_middle_name ELSE '' END ||
        ' ' || chosen_last_name
    );
END;
$$;

CREATE OR REPLACE PROCEDURE generate_address(
    IN seed BIGINT, IN locale VARCHAR(10), IN batch_index INT, IN row_index INT,
    IN arr_streets TEXT[], IN arr_city_names TEXT[], IN arr_city_regions TEXT[], IN arr_city_postals TEXT[],
    OUT address TEXT
) LANGUAGE plpgsql AS $$
DECLARE
    u DOUBLE PRECISION; digit_rand DOUBLE PRECISION;
    house_num INT; idx_city INT;
    street TEXT; city TEXT; region TEXT; postal_pattern TEXT;
    postal_code TEXT := ''; char CHAR; idx INT;
BEGIN
    u := rng(seed, locale, batch_index, row_index, 7);
    house_num := floor(u * 999) + 1;

    u := rng(seed, locale, batch_index, row_index, 8);
    street := arr_streets[ LEAST(1 + floor(u * array_length(arr_streets, 1))::INT, array_length(arr_streets, 1)) ];

    u := rng(seed, locale, batch_index, row_index, 9);
    idx_city := LEAST(1 + floor(u * array_length(arr_city_names, 1))::INT, array_length(arr_city_names, 1));
    city := arr_city_names[idx_city];
    region := arr_city_regions[idx_city];
    postal_pattern := arr_city_postals[idx_city];

    FOR idx IN 1 .. length(postal_pattern) LOOP
        char := substr(postal_pattern, idx, 1);
        IF char = '#' THEN
            digit_rand := rng(seed, locale, batch_index, row_index, 100 + idx);
            postal_code := postal_code || floor(digit_rand * 10)::text;
        ELSE
            postal_code := postal_code || char;
        END IF;
    END LOOP;

    address := house_num::text || ' ' || street || ', ' || city || ', ' || region || ' ' || postal_code;
END;
$$;

CREATE OR REPLACE PROCEDURE generate_geolocation(
    IN seed BIGINT, IN locale VARCHAR(10), IN batch_index INT, IN row_index INT,
    OUT lat NUMERIC(10, 6), OUT lon NUMERIC(10, 6)
) LANGUAGE plpgsql AS $$
DECLARE
    u1 DOUBLE PRECISION; u2 DOUBLE PRECISION;
BEGIN
    u1 := rng(seed, locale, batch_index, row_index, 12);
    lon := (u1 * 360.0 - 180.0)::NUMERIC(10, 6);

    u2 := rng(seed, locale, batch_index, row_index, 13);
    lat := degrees(asin(2.0 * u2 - 1.0))::NUMERIC(10, 6);
END;
$$;

CREATE OR REPLACE PROCEDURE generate_height(
    IN seed BIGINT, IN locale VARCHAR(10), IN batch_index INT, IN row_index INT,
    OUT height_cm INT
) LANGUAGE plpgsql AS $$
DECLARE
    u1 DOUBLE PRECISION;
BEGIN
    CALL rnorm(seed, locale, batch_index, row_index, 14, 175.0, 10.0, u1);
    height_cm := round(u1)::INT;
END;
$$;

CREATE OR REPLACE PROCEDURE generate_weight(
    IN seed BIGINT, IN locale VARCHAR(10), IN batch_index INT, IN row_index INT,
    OUT weight_kg FLOAT
) LANGUAGE plpgsql AS $$
DECLARE
    u2 DOUBLE PRECISION;
BEGIN
    CALL rnorm(seed, locale, batch_index, row_index, 16, 75.0, 15.0, u2);
    weight_kg := round(u2 * 10) / 10.0;
END;
$$;

CREATE OR REPLACE PROCEDURE generate_eye_color(
    IN seed BIGINT, IN locale VARCHAR(10), IN batch_index INT, IN row_index INT,
    IN arr_eyes TEXT[],
    OUT eye_color TEXT
) LANGUAGE plpgsql AS $$
DECLARE
    u_eye DOUBLE PRECISION;
BEGIN
    u_eye := rng(seed, locale, batch_index, row_index, 18);
    eye_color := arr_eyes[ LEAST(1 + floor(u_eye * array_length(arr_eyes, 1))::INT, array_length(arr_eyes, 1)) ];
END;
$$;

CREATE OR REPLACE PROCEDURE generate_hair_color(
    IN seed BIGINT, IN locale VARCHAR(10), IN batch_index INT, IN row_index INT,
    IN arr_hair TEXT[],
    OUT hair_color TEXT
) LANGUAGE plpgsql AS $$
DECLARE
    u_hair DOUBLE PRECISION;
BEGIN
    u_hair := rng(seed, locale, batch_index, row_index, 19);
    hair_color := arr_hair[ LEAST(1 + floor(u_hair * array_length(arr_hair, 1))::INT, array_length(arr_hair, 1)) ];
END;
$$;

CREATE OR REPLACE PROCEDURE generate_physical_attributes(
    IN seed BIGINT, IN locale VARCHAR(10), IN batch_index INT, IN row_index INT,
    IN arr_eyes TEXT[], IN arr_hair TEXT[],
    OUT height_cm INT, OUT weight_kg FLOAT, OUT eye_color TEXT, OUT hair_color TEXT
) LANGUAGE plpgsql AS $$
BEGIN
    CALL generate_height(seed, locale, batch_index, row_index, height_cm);
    CALL generate_weight(seed, locale, batch_index, row_index, weight_kg);
    CALL generate_eye_color(seed, locale, batch_index, row_index, arr_eyes, eye_color);
    CALL generate_hair_color(seed, locale, batch_index, row_index, arr_hair, hair_color);
END;
$$;

CREATE OR REPLACE PROCEDURE generate_phone(
    IN seed BIGINT, IN locale VARCHAR(10), IN batch_index INT, IN row_index INT,
    IN arr_phones TEXT[],
    OUT phone TEXT
) LANGUAGE plpgsql AS $$
DECLARE
    u DOUBLE PRECISION; digit_rand DOUBLE PRECISION;
    phone_pattern TEXT; char CHAR; idx INT;
BEGIN
    u := rng(seed, locale, batch_index, row_index, 20);
    phone_pattern := arr_phones[ LEAST(1 + floor(u * array_length(arr_phones, 1))::INT, array_length(arr_phones, 1)) ];

    phone := '';
    FOR idx IN 1 .. length(phone_pattern) LOOP
        char := substr(phone_pattern, idx, 1);
        IF char = '#' THEN
            digit_rand := rng(seed, locale, batch_index, row_index, 200 + idx);
            phone := phone || floor(digit_rand * 10)::text;
        ELSE
            phone := phone || char;
        END IF;
    END LOOP;
END;
$$;

CREATE OR REPLACE PROCEDURE generate_email(
    IN seed BIGINT, IN locale VARCHAR(10), IN batch_index INT, IN row_index INT,
    IN arr_domains TEXT[], IN full_name TEXT,
    OUT email TEXT
) LANGUAGE plpgsql AS $$
DECLARE
    u DOUBLE PRECISION; domain TEXT;
    first_name TEXT; last_name TEXT; name_parts TEXT[];
BEGIN
    u := rng(seed, locale, batch_index, row_index, 21);
    domain := arr_domains[ LEAST(1 + floor(u * array_length(arr_domains, 1))::INT, array_length(arr_domains, 1)) ];

    name_parts := string_to_array(full_name, ' ');
    IF array_length(name_parts, 1) > 2 THEN
        first_name := name_parts[2];
        last_name := name_parts[array_length(name_parts, 1)];
    ELSIF array_length(name_parts, 1) > 1 THEN
        first_name := name_parts[1];
        last_name := name_parts[array_length(name_parts, 1)];
    ELSE
        first_name := full_name;
        last_name := 'mail';
    END IF;

    email := LOWER(first_name || '.' || last_name || (round(rng(seed, locale, batch_index, row_index, 99) * 1000))::text || '@' || domain);
END;
$$;

CREATE OR REPLACE FUNCTION generate_users_batch(
    p_seed BIGINT,
    p_locale VARCHAR(10),
    p_batch_index INT,
    p_batch_size INT DEFAULT 10
)
RETURNS TABLE (
    id BIGINT,
    batch_index INT,
    row_index INT,
    full_name TEXT,
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(200),
    height_cm INT,
    weight_kg FLOAT,
    eye_color VARCHAR(30),
    hair_color VARCHAR(30),
    latitude NUMERIC(10, 6),
    longitude NUMERIC(10, 6)
)
LANGUAGE plpgsql AS $$
DECLARE
    row_idx INT;
    
    arr_titles TEXT[]; arr_fn TEXT[]; arr_ln TEXT[]; arr_streets TEXT[];
    arr_city_names TEXT[]; arr_city_regions TEXT[]; arr_city_postals TEXT[];
    arr_phones TEXT[]; arr_domains TEXT[]; arr_eyes TEXT[]; arr_hair TEXT[];
    
    v_full_name TEXT; v_address TEXT; v_lat NUMERIC(10, 6); v_lon NUMERIC(10, 6);
    v_height_cm INT; v_weight_kg FLOAT; v_eye_color TEXT; v_hair_color TEXT; v_phone TEXT; v_email TEXT;
BEGIN
    CREATE TEMPORARY TABLE IF NOT EXISTS users (
        id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
        batch_index INT, row_index INT, full_name TEXT, address TEXT,
        phone VARCHAR(20), email VARCHAR(200), height_cm INT, weight_kg FLOAT,
        eye_color VARCHAR(30), hair_color VARCHAR(30), latitude NUMERIC(10, 6), longitude NUMERIC(10, 6)
    );

    DELETE FROM users;

    SELECT array_agg(title_text) INTO arr_titles FROM lookup_titles WHERE locale_code = p_locale;
    SELECT array_agg(first_name) INTO arr_fn FROM lookup_first_names WHERE locale_code = p_locale;
    SELECT array_agg(last_name) INTO arr_ln FROM lookup_last_names WHERE locale_code = p_locale;
    SELECT array_agg(street_name) INTO arr_streets FROM lookup_streets WHERE locale_code = p_locale;
    
    SELECT array_agg(city_name), array_agg(state_or_region), array_agg(postal_code_pattern) 
    INTO arr_city_names, arr_city_regions, arr_city_postals FROM lookup_cities WHERE locale_code = p_locale;
    
    SELECT array_agg(format_pattern) INTO arr_phones FROM lookup_phone_formats WHERE locale_code = p_locale;
    SELECT array_agg(domain_name) INTO arr_domains FROM lookup_email_domains WHERE locale_code = p_locale;
    SELECT array_agg(color_name) INTO arr_eyes FROM lookup_eye_colors WHERE locale_code = p_locale;
    SELECT array_agg(color_name) INTO arr_hair FROM lookup_hair_colors WHERE locale_code = p_locale;

    FOR row_idx IN 0 .. (p_batch_size - 1) LOOP
        CALL generate_full_name(p_seed, p_locale, p_batch_index, row_idx, arr_titles, arr_fn, arr_ln, v_full_name);
        CALL generate_address(p_seed, p_locale, p_batch_index, row_idx, arr_streets, arr_city_names, arr_city_regions, arr_city_postals, v_address);
        CALL generate_geolocation(p_seed, p_locale, p_batch_index, row_idx, v_lat, v_lon);
        CALL generate_physical_attributes(p_seed, p_locale, p_batch_index, row_idx, arr_eyes, arr_hair, v_height_cm, v_weight_kg, v_eye_color, v_hair_color);
        CALL generate_phone(p_seed, p_locale, p_batch_index, row_idx, arr_phones, v_phone);
        CALL generate_email(p_seed, p_locale, p_batch_index, row_idx, arr_domains, v_full_name, v_email);
        
        INSERT INTO users (
            batch_index, row_index, full_name, address, phone, email,
            height_cm, weight_kg, eye_color, hair_color, latitude, longitude
        ) VALUES (
            p_batch_index, row_idx, v_full_name, v_address, v_phone, v_email,
            v_height_cm, v_weight_kg, v_eye_color, v_hair_color, v_lat, v_lon
        );  
    END LOOP;

    RETURN QUERY SELECT * FROM users ORDER BY users.row_index ASC;
END;
$$;