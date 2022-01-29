SELECT id, code2
FROM
    courses
INNER JOIN course_codes USING (id)
WHERE REGEXP_LIKE(code2, '^(c).*')
group by id