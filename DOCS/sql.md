docker exec -i test-wine_host-1 psql -U wine -d wine_db -c "
SELECT d.lwin, l.sub_type, s.name, d.subcategory_id
FROM drinks d
JOIN lwins l ON d.lwin = l.lwin
JOIN subcategories s ON d.subcategory_id = s.id
WHERE COALESCE(l.sub_type,'') <> COALESCE(s.name, '');
"

docker exec -i test-wine_host-1 psql -U wine -d wine_db -c "
SELECT DISTINCT l.sub_type, l.type
FROM lwins l
"

docker exec -i test-wine_host-1 psql -U wine -d wine_db -c "
UPDATE lwins
SET type = 'Fortified Wine', sub_type = 'Port'
WHERE type = 'Port' AND sub_type IS NULL;
"

docker exec -i test-wine_host-1 psql -U wine -d wine_db -c "
UPDATE lwins
SET type = 'Fortified Wine', sub_type = NULL
WHERE type = 'Port' AND sub_type = 'Fortified Wine';
"

docker exec -i test-wine_host-1 psql -U wine -d wine_db -c "
UPDATE lwins
SET type = 'Fortified Wine'
WHERE type = 'Port';
"

--------------BRANDY - Cognac-----------
docker exec -i test-wine_host-1 psql -U wine -d wine_db -c "
SELECT d.lwin, l.type, l.region, s.name, d.subcategory_id, c.name
FROM drinks d
JOIN lwins l ON d.lwin = l.lwin
JOIN subcategories s ON d.subcategory_id = s.id
JOIN categories c ON s.category_id = c.id
WHERE d.subcategory_id = 2 AND l.region <> COALESCE('Cognac', '');
"
-----------------------------------------------------------
docker exec -i test-wine_host-1 psql -U wine -d wine_db -c "
SELECT DISTINCT l.sub_type, l.type, count(*)
FROM lwins l WHERE type = 'Brandy' GROUP BY l.sub_type, l.type;
"

----------------Cognac---------------------
docker exec -i test-wine_host-1 psql -U wine -d wine_db -c "
UPDATE lwins
SET type = 'Brandy', sub_type = NULL
WHERE type = 'Cognac';
"

docker exec -i test-wine_host-1 psql -U wine -d wine_db -c "
UPDATE lwins
SET sub_type = region
WHERE type = 'Brandy' AND region IN ('Cognac', 'Armagnac');
"

docker exec -i test-wine_host-1 psql -U wine -d wine_db -c "
UPDATE lwins
SET sub_type = 'Calvados'
WHERE type = 'Brandy' AND sub_region LIKE 'Calvados%';
"

docker exec -i test-wine_host-1 psql -U wine -d wine_db -c "
UPDATE lwins
SET sub_type = 'Grappa'
WHERE type = 'Brandy' AND sub_region LIKE 'Grappa%';
"

docker exec -i test-wine_host-1 psql -U wine -d wine_db -c "
UPDATE lwins
SET sub_type = 'Brandy de Jerez'
WHERE type = 'Brandy' AND sub_region LIKE '%Jerez';
"

docker exec -i test-wine_host-1 psql -U wine -d wine_db -c "
UPDATE lwins
SET sub_type = 'Eau-de-vie'
WHERE type = 'Brandy' AND sub_region LIKE 'Eau-de-vie%';
"

docker exec -i test-wine_host-1 psql -U wine -d wine_db -c "
UPDATE lwins
SET sub_type = 'Fine'
WHERE type = 'Brandy' AND sub_region LIKE 'Fine %';
"

docker exec -i test-wine_host-1 psql -U wine -d wine_db -c "
UPDATE lwins
SET sub_type = 'Marc'
WHERE type = 'Brandy' AND sub_region LIKE 'Marc %';
"

--------update bitters->bitter, liqueur->Liquer
docker exec -i test-wine_host-1 psql -U wine -d wine_db -c "
UPDATE drinks
SET subcategory_id=11
WHERE subcategory_id=97
"

-----------
docker exec -i test-wine_host-1 psql -U wine -d wine_db -c "
SELECT l.lwin, l.sub_type, s.name, s.id
FROM lwins l
JOIN subcategories s ON l.sub_type = s.name
WHERE l.type = 'Brandy';
"

docker exec -i test-wine_host-1 psql -U wine -d wine_db -c "
UPDATE drinks d
SET subcategory_id = s.id
FROM lwins l
JOIN subcategories s ON l.sub_type = s.name
WHERE d.lwin = l.lwin
AND l.type = 'Brandy';;
"
