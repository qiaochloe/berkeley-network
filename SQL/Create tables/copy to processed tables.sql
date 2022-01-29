set sql_safe_updates = 0;

delete from courses_p;
insert into courses_p 
select * from courses;

delete from course_codes_p;
insert into course_codes_p
select * from course_codes;

delete from prereqs_p;
insert into prereqs_p
select * from prereqs;

set sql_safe_updates = 1;