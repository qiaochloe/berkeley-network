DROP TABLE IF EXISTS `courses_p`;
CREATE TABLE `courses_p` (
   `id` int NOT NULL auto_increment,
   `title` varchar(256) NOT NULL,
   `description` varchar(2560) NOT NULL,
   `units` int NOT NULL,
   `level` varchar(256) NOT NULL,
   `fall` tinyint(1) DEFAULT '0',
   `spring` tinyint(1) DEFAULT '0',
   `summer` tinyint(1) DEFAULT '0',
   `grading` varchar(256) DEFAULT NULL,
   `final` varchar(256) DEFAULT NULL,
   `division` varchar(256) DEFAULT NULL,
   PRIMARY KEY (`id`)
 );
 
 DROP TABLE IF EXISTS `course_codes_p`;
 CREATE TABLE `course_codes_p` (
   `id` int NOT NULL,
   `course_code_id` int NOT NULL auto_increment,
   `full_code` varchar(256) NOT NULL,
   `code1` varchar(256) NOT NULL,
   `code2` varchar(256) NOT NULL,
   PRIMARY KEY (`course_code_id`)
 );
 
 DROP TABLE IF EXISTS `prereqs_p`;
 CREATE TABLE `prereqs_p` (
   `id` int NOT NULL,
   `prereq` varchar(2560) NOT NULL,
   `flag` boolean DEFAULT true
 );