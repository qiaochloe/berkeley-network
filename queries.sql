---- @block 
--DELETE courses_processed FROM courses_processed
--INNER JOIN(
--    SELECT title,COUNT(*) c
--    FROM courses_processed 
--    WHERE units <= 1
--    GROUP BY title 
--    ORDER BY c DESC) tmp
--ON courses_processed.title = tmp.title
--where c >= 10

-- @block
DELETE 
FROM courses_processed
WHERE code2 IN (24, 39, 84, 97, 98, 99, 197, 198, 199)
