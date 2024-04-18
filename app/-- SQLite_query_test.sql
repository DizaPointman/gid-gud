-- SQLite
SELECT id, name, user_id, parent_id
FROM category

WHERE id != 7 AND parent_id IS NULL AND lower(name) NOT LIKE lower('%default%');