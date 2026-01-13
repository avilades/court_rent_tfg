
/*
Creamos una secuencia para el campo price_id
*/
CREATE SEQUENCE seq_price_priceid START 1;

/*
Asignar el valor por defecto de la secuencia
*/
ALTER TABLE prices ALTER COLUMN price_id SET DEFAULT nextval('seq_price_priceid');

/*
(Opcional) Reiniciar la secuencia para que comience con el siguiente valor disponible
*/
SELECT setval('seq_price_priceid', COALESCE(MAX(price_id), 0) + 1) FROM prices;

INSERT INTO prices (amount,start_date,end_date,description) VALUES (10,'2026-01-01',NULL,'Precio baja ocupacion');
INSERT INTO prices (amount,start_date,end_date,description) VALUES (20,'2026-01-01',NULL,'Precio por defecto');
INSERT INTO prices (amount,start_date,end_date,description) VALUES (30,'2026-01-01',NULL,'Precio alta ocupacion');    