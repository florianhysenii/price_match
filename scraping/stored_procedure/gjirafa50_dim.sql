DELIMITER $$

CREATE PROCEDURE update_dim_gjirafa50_products_auto()
BEGIN
    DECLARE v_current_date DATE;
    SET v_current_date = CURDATE();

    -- Update `valid_to` for records where any field has changed (name, price, promo_price, image_url, product_url)
    UPDATE dim_gjirafa50_products tgt
    JOIN gjirafa50_products src
    ON tgt.product_id = src.product_id
    SET tgt.valid_to = v_current_date
    WHERE tgt.valid_to IS NULL
    AND (tgt.name != src.name OR tgt.price != src.price OR tgt.promo_price != src.promo_price
    OR tgt.image_url != src.image_url OR tgt.product_url != src.product_url);

    -- Insert new records from `gjirafa50_products` where changes have been detected
    INSERT INTO dim_gjirafa50_products (product_id, name, price, promo_price, image_url, product_url, valid_from)
    SELECT src.product_id, src.name, src.price, src.promo_price, src.image_url, src.product_url, v_current_date
    FROM gjirafa50_products src
    LEFT JOIN dim_gjirafa50_products tgt
    ON src.product_id = tgt.product_id
    WHERE tgt.valid_to = v_current_date;

END$$

DELIMITER ;


/*step 1

INSERT INTO dim_gjirafa50_products (product_id, name, price, promo_price, image_url, product_url, valid_from)
SELECT product_id, name, price, promo_price, image_url, product_url, CURDATE()
FROM gjirafa50_products;

step 2
when updating the data then this will track the changes

CALL update_dim_gjirafa50_products_auto();
note
this will be called when scraper will finish the work