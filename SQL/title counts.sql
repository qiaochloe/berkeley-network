SELECT title,COUNT(*) c
FROM courses_processed 
WHERE units <= 1
GROUP BY title 
ORDER BY c DESC