# User Generation Documentation

FUNCTION rng
Generates and returns a pseudo-random double precision number between 0 and 1.
Params:
- seed BIGINT: Set seed.
- locale VARCHAR(10): The locale string.
- batch_index INT: Current batch identifier.
- row_index INT: Current row identifier.
- identifier INT: Unique step identifier for random generation.

This function acts as a seeded uniform random number generator, returning a value from 0 to 1. All input parameters are put into hash (using `hashtext()`), turned positive and divided by $2^{32}$.

---

PROCEDURE rnorm
Generates a random double precision number from normal distribution.
Params:
- seed BIGINT: Set seed.
- locale VARCHAR(10): The locale string.
- batch_index INT: Current batch identifier.
- row_index INT: Current row identifier.
- identifier INT: Unique step identifier for random generation.
- mean DOUBLE PRECISION: The desired mean ($\mu$) of the normal distribution.
- std DOUBLE PRECISION: The desired standard deviation ($\sigma$) of the normal distribution.
- out_random_normal OUT DOUBLE PRECISION: The resulting random variable.

This procedure uses the Box-Muller transform to generate normally distributed random numbers. Using the `rng` function, the procedures generates random numbers put in the formula $Z = \sqrt{-2 \ln(U_1)} \cos(2 \pi U_2)$. Since $Z$ is from a standard normal distribution, the result $X$ calculated by $X = \mu + \sigma Z$ is from a normal distribution of mean $\mu$ and standard deviation $\sigma$.

---

PROCEDURE generate_full_name
Generates a full name including optional titles and middle names.
Params:
- seed BIGINT: Set seed.
- locale VARCHAR(10): The locale string.
- batch_index INT: Current batch identifier.
- row_index INT: Current row identifier.
- arr_titles TEXT[]: Array of titles.
- arr_fn TEXT[]: Array of first names.
- arr_ln TEXT[]: Array of last names.
- full_name OUT TEXT: Full name.

The procedure randomly picks elements from lookup first name, last name and title tables. It enforces a $5\%$ probability threshold for assigning a title, and a $5\%$ probability for assigning a middle name.

---

PROCEDURE generate_address
Generates a localized physical address.
Params:
- seed BIGINT: Set seed.
- locale VARCHAR(10): The locale string.
- batch_index INT: Current batch identifier.
- row_index INT: Current row identifier.
- arr_streets TEXT[]: Array of street names.
- arr_city_names TEXT[]: Array of city names.
- arr_city_regions TEXT[]: Array of states/regions.
- arr_city_postals TEXT[]: Array of postal code patterns.
- address OUT TEXT: Full address string.

The house number is randomly selected in the range $1$ to $999$ using a uniform distribution. The algorithm selects a single random index `idx_city` to simultaneously pull matching elements from `arr_city_names`, `arr_city_regions`, and `arr_city_postals`. The procedure replaces `#` in postal codes with random numbers between $0$ and $9$.

---

PROCEDURE generate_geolocation
Generates geographic coordinates on a spherical globe.
Params:
- seed BIGINT: Set seed.
- locale VARCHAR(10): The locale string.
- batch_index INT: Current batch identifier.
- row_index INT: Current row identifier.
- lat OUT NUMERIC(10, 6): Latitude coordinate.
- lon OUT NUMERIC(10, 6): Longitude coordinate.

The procedure generates coordinates according to spherical area - longitude is calculated from $\lambda = U_1 \times 360 - 180$ and latitude is generated using $\phi = \arcsin(2 U_2 - 1)$, where $U_1, U_2$ are randomly generated numbers using `rng`. The output is converted from radians to degrees.

---

PROCEDURE generate_height
Generates a human height in centimeters.
Params:
- seed BIGINT: Set seed.
- locale VARCHAR(10): The locale string.
- batch_index INT: Current batch identifier.
- row_index INT: Current row identifier.
- height_cm OUT INT: Height in cm.

The procedure generates a randomly distributed number of mean ($\mu = 175$) and standard deviation ($\sigma = 10$).

---

PROCEDURE generate_weight
Generates a realistic human body weight in kilograms.
Params:
- seed BIGINT: Set seed.
- locale VARCHAR(10): The locale string.
- batch_index INT: Current batch identifier.
- row_index INT: Current row identifier.
- weight_kg OUT FLOAT: Weight in kg.

The procedure generates a randomly distributed number of mean ($\mu = 75$) and standard deviation ($\sigma = 15$).

---

PROCEDURE generate_eye_color
Returns a random eye color from list.
Params:
- seed BIGINT: Set seed.
- locale VARCHAR(10): The locale string.
- batch_index INT: Current batch identifier.
- row_index INT: Current row identifier.
- arr_eyes TEXT[]: Array of eye colors.
- eye_color OUT TEXT: Chosen eye color.

Randomly chooses an eye color from the `arr_eyes` array.

---

PROCEDURE generate_hair_color
Returns a random hair color from a list.
Params:
- seed BIGINT: Set seed.
- locale VARCHAR(10): The locale string.
- batch_index INT: Current batch identifier.
- row_index INT: Current row identifier.
- arr_hair TEXT[]: Array of available hair colors.
- hair_color OUT TEXT: Chosen hair color.

Randomly chooses a hair color from the `arr_hair` array.

---

PROCEDURE generate_physical_attributes
Generates human physical attributes: height, weight, eye color, and hair color.
Params:
- seed BIGINT: Set seed.
- locale VARCHAR(10): The locale string.
- batch_index INT: Current batch identifier.
- row_index INT: Current row identifier.
- arr_eyes TEXT[]: Array of eye colors.
- arr_hair TEXT[]: Array of hair colors.
- height_cm OUT INT: Generated height.
- weight_kg OUT FLOAT: Generated weight.
- eye_color OUT TEXT: Generated eye color.
- hair_color OUT TEXT: Generated hair color.

The procedure is a wrapper for calling procedures and reaturning their results: `generate_height`, `generate_weight`, `generate_eye_color`, and `generate_hair_color`.

---

PROCEDURE generate_phone
Generates a randomly formatted phone number.
Params:
- seed BIGINT: Set seed.
- locale VARCHAR(10): The locale string.
- batch_index INT: Current batch identifier.
- row_index INT: Current row identifier.
- arr_phones TEXT[]: Array of phone numbers patterns.
- phone OUT TEXT: Phone number.

Randomly selects a phone format from the array, then loops over the characters and replaces `#` with numbers generated via `rng`.

---

PROCEDURE generate_email
Generates an email address from the user's name.
Params:
- seed BIGINT: Set seed.
- locale VARCHAR(10): The locale string.
- batch_index INT: Current batch identifier.
- row_index INT: Current row identifier.
- arr_domains TEXT[]: Array of valid email domains.
- full_name TEXT: The previously generated full name.
- email OUT TEXT: Email address.

The procedure uses the `full_name` to generate a user e-mail, adds a random integer from $0$ to $999$, attaches the `@` sign and a randomly selected domain from `arr_domains`.

---

FUNCTION generate_users_batch
Main function that generates a complete batch of users as a returned table.
Params:
- p_seed BIGINT: Set seed.
- p_locale VARCHAR(10): The locale string (e.g. 'en_US').
- p_batch_index INT: Current batch identifier.
- p_batch_size INT DEFAULT 10: Size of one user generation batch.

The function creates a temporary table `users` on the fly to hold the output. It queries the `lookup_*` tables and places them into array variables. It then iterates from $0$ to $(\text{p_batch_size} - 1)$, and in each iteration, it calls the generation procedures (`generate_full_name`, `generate_address`, etc.) to constructs a full row of fake user information, which is inserted into the temporary table. The function returns the generated dataset queried from the temporary table.