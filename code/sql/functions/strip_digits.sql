DROP FUNCTION IF EXISTS strip_digits;

CREATE FUNCTION strip_digits(input_text VARCHAR(255))
RETURNS VARCHAR(255)
DETERMINISTIC
NO SQL
	RETURN REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
		REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
			TRIM(input_text),
			'0', ''), '1', ''), '2', ''), '3', ''), '4', ''),
			'5', ''), '6', ''), '7', ''), '8', ''), '9', '');

-- Random test
SELECT strip_digits(' 123ABC-45X ') AS item_number_suff;

-- Test on data
SELECT
	item_number,
	strip_digits(item_number) AS item_number_suff
FROM items_clean;