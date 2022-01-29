/*
TO DO 
- Create new table for Cross-Listed courses (C)
- Delete Honors courses (H)
- Delete Summer Session courses (N)
- Remove Reading and Composition prefix (R)
- Remove American Cultures suffix (AC)
- Merge multi-term courses (A-C suffixes)
- Merge courses and labs (L suffix)
- Sort by lower division (1-99), upper division (100-199), graduate (200-299), professional (300-499)
- Delete Individual Study and Research Graduate courses (500-699)
*/

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
/* Deletes
- 24 Freshman Seminars
- 39 Freshman/Sophomore Seminars
- 84 Sophomore Seminars
- 97 Field Studies Courses at the lower-division level
- 98 Directed Group Study at the lower-division level
- 99 Supervised Independent Study at the lower-division level 
- 197 Field Studies courses at the upper-division level
- 198 Organized Group Study at the upper-division level
- 199 Supervised Independent Study at the upper-division level
*/

DELETE 
FROM courses_processed
WHERE code2 IN (24, 39, 84, 97, 98, 99, 197, 198, 199)

-- @block 
