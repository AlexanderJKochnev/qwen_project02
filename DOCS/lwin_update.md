## ---------------------
"lwin"
"source_id"
"first_vintage": 1000,
"last_vintage": 1000,
"display_name"
"title"     wine 
"subtitle"
"producer_id"
"classification_id"
"vintageconfig_id"
"designation_id"

"site_id":
      "subregion_id":
        "region_id":
          "country_id"
"parcel_id"
"subcategory_id":
      "category_id": 
# sql -------------------------------------------------------------------------
docker exec -i test-wine_host-1 psql -U wine -d wine_db -c "
INSERT INTO drinks (lwin, source_id, first_vintage, last_vintage, display_name, title, subtitle, producer_id, classification_id, vintageconfig_id, designation_id, site_id, parcel_id, subcategory_id)
SELECT 
lwin, 
2, 
first_vintage, final_vintage, 
display_name, 
trim(COALESCE(wine, (string_to_array(display_name, ','))[cardinality(string_to_array(display_name, ','))])), 
trim(CONCAT_WS(' ', producer_title, producer_name)), 
p.id AS producer, 
c.id, 
v.id, 
d.id, 
st.id, 
pa.id, 
sc.id
FROM lwins
LEFT JOIN producers p ON p.name = lwins.producer_name
LEFT JOIN classifications c ON c.name = lwins.classification
LEFT JOIN vintageconfigs v ON v.name = lwins.vintage_config
LEFT JOIN designations d ON d.name = lwins.designation
LEFT JOIN countries co ON co.name = lwins.country 
LEFT JOIN regions r ON 
    (r.name IS NOT DISTINCT FROM lwins.region) AND 
    (r.country_id = co.id)
LEFT JOIN subregions sr ON 
    (sr.name IS NOT DISTINCT FROM lwins.sub_region) AND 
    (sr.region_id = r.id)
LEFT JOIN sites st ON 
    (st.name IS NOT DISTINCT FROM lwins.site) AND 
    (st.subregion_id = sr.id)
LEFT JOIN parcels pa ON pa.name = lwins.parcel
LEFT JOIN categories cat ON cat.name = lwins.type
LEFT JOIN subcategories sc ON 
    (sc.name IS NOT DISTINCT FROM lwins.sub_type) AND 
    (sc.category_id = cat.id)
WHERE (lwins.country IS NOT NULL AND lwins.country <> '')
AND (lwins.type IS NOT NULL AND lwins.type <>'')
ON CONFLICT (title, subtitle, producer_id, site_id, parcel_id, lwin, anno, display_name) DO NOTHING;
"

--------------------------------
## ПЕРЕОПРЕДЕЛЯЕМ СЧЕТЧИК
docker exec -i test-wine_host-1 psql -U wine -d wine_db -c "
WITH updated AS (
    SELECT id, 149 + row_number() OVER (ORDER BY id) as new_id
    FROM drinks
    WHERE id > 149
)
UPDATE drinks
SET id = updated.new_id
FROM updated
WHERE drinks.id = updated.id;

-- 2. Устанавливаем счетчик на следующее свободное число после перенумерации
SELECT setval('drinks_id_seq', (SELECT max(id) FROM drinks));
"