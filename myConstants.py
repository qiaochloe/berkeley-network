# Stores constants to keep other files clear 

import string 
ALPHA = string.ascii_lowercase

# SCRAPER CONSTANTS
# Remove letters to skip them 
LETTERS = 'abcdefghijklmnopqrstuvwxyz'
DIR_URL = "http://guide.berkeley.edu/courses/"
ROOT_URL = "http://guide.berkeley.edu"
SCHOOL_YEAR = 2021

# Official short code : alt code
# Cannot currently handle multiple alternates 
ALT_CATEGORY_DICT = {"biology":"bio", "bio eng":"bioe", "compsci":"cs", "mec eng":"me", "el eng":"ee", "civ eng":"ce"}

# PROCESSER.PY CONSTANTS
# Codes to be deleted, regardless of suffix or prefix 
DELETE_CODES = ['24', '39', '84', '97', '98', '99', '197', '198', '199']

# All courses with these prefixes will be deleted 
DELETE_PREFIXES = ['h', 'n']

# Remove these prefixes from course codes
REMOVE_PREFIXES = ['r'] 

# Remove these suffixes from course codes
REMOVE_SUFFIXES = ['ac']

# 3d array with each tuple corresponding to a column in courses_p
# The first element of the tuple is the table name 
# The second element is a dictionary of what each possible value should be changed to
FIELDS_DICT = [('level', 
                    {'graduate':'graduate', 
                    'professional course for teachers or prospective teachers':'professional', 
                    'other professional':'professional', 
                    'graduate examination preparation':'delete', 
                    'undergraduate':'undergraduate'}),
                ('grading', 
                    {'letter grade':'letter grade',
                    'offered for satisfactory/unsatisfactory grade only':'pass/fail',
                    'offered for pass/not pass grade only':'pass/fail',
                    'the grading option will be decided by the instructor when the class is offered':'undecided'}),
                    # Ignoring one/two year courses for now 
                ('final', 
                    {'final exam not required':'final exam not required',
                    'final exam required':'final exam required',
                    'alternative to final exam':'alternative to final exam',
                    'final exam to be decided by the instructor when the class is offered':'undecided',
                    'final exam required, with common exam group':'group final exam'})]
                    # Ignoring one/two year courses for now

DELETE_PREREQS = [
                    'consent of instructor', 
                    'consent of instructor or director',
                    'this course is open to graduate students, with priority given to students in mechanical engineering’s master of engineering program',
                    'priority given to freshmen and sophomores',
                    'upper division status',
                    'at the discretion of the instructor',
                    'at discretion of instructor',
                    'graduate standing',
                    'enrollment is strictly limited to and required of all anthropology and medical anthropology graduate s tudents who have not been advanced to candidacy',
                    'graduate standing',
                    'limited to senior honors candidates',
                    'doctoral candidate',
                    'm.s. or ph.d. standing',
                    'advancement to candidacy or instructor permission',
                    'primarily for juniors and seniors in the major',
                    'senior standing and qualifying scholastic record',
                    'appointment as a graduate student instructor',
                    'graduate student researcher appointment',
                    'equivalent',
                    'reading and composition requirement satisfied',
                    'satisfaction of the reading and composition requirement',
                    'reading and composition requirement',
                    'those set by instructor',
                    'determined by offering',
                    'regulations set by college of letters and science'
                ]

DELETE_PREREQ_SENTENCE = ['score', 'though neither is required']

IGNORE_ABBREVS = ['ph.d', 'ph.d.', 'e.g.'] 

PLACEHOLDER = 'PLACEHOLDER'