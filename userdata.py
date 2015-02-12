# -*- coding: utf-8 -*-
"""
Convert "clusterusers.csv" to "people.rst"

@author: JBeeck
"""

# ==============================================================================
# read CSV -> dict
# ==============================================================================

# read-in current list of people
data = open('clusterusers.csv','r').read().split('\n')

# line info is on the first line, remove comment column
what = data[0].split(',')
what = [i for i in what if i not in ['comments\r']]
# username is the thing to store data with: find which field this is
# find the index
usernamefield = [i for (i,field) in enumerate(what) if field in ('username')][0]
# first two lines are not people
peopledata = data[2:]

# read "data" to dictionary "users"
# key:    'username'
# fields: 'First Name','Last Name','username','email address','software'
users = dict()
for person in peopledata:
  try:
    # split person into data fields
    persondata = person.split(',')
    # store the user in the users dictionary in the field 'username'
    # stored as a dictionary of all fields in persondata
    users[persondata[usernamefield]] = {field:persondata[i].replace(';','; ') for (i,field) in enumerate(what)}
  except:
    pass

# ==============================================================================
# convert names: email -> lowercase, organize by software, username->prog.string
# ==============================================================================

# convert e-mail
for user in users:
  users[user]['email address'] = users[user]['email address'].lower()

# convert output format of the username
for user in users:
  if len(user)>0:
    users[user]['username'] = '``'+user+'``'

# programs dictionary
programs = {'MATLAB':('matlab'),
            'MSC.Marc':('marc','mentat','msc marc','msc.marc','marcmentat','marc+subroutines','marcmentat+subroutines','msc.marc+subroutines'),
            'Abaqus':('abaqus','abaqus+subroutines','abaqus+subroutines'),
            'Python':('Python','python','Python (limited)','python (limited)'),
            'DAWN':('Dawn'),
            'Linux/Bash':('Linux/Bash','linux','Bash','bash','Linux'),
            'TFEM':('TFEM','tfem','Tfem'),
            'C':('C','c'),
            'C++':('C++','c++'),
            'Fortran':('fortran','Fortran','Fortran90','fortran90'),
            'SEPRAN':('SEPRAN','sepran'),
            'Mathematica':('Mathematica','mathematica')}

progsort = ['Linux/Bash','Python','MATLAB','Mathematica','C','C++','Fortran','Abaqus','MSC.Marc','TFEM','DAWN','SEPRAN']

# find programs by the programs dictionary (unknown alternatives are not listed)
# empty software dictionary for each software program
software = {program:[] for program in programs}
# check software for each user and add to software list the username
for user in users:
    softwarelist = users[user]['software'].split('; ')
    for softwarename in softwarelist:
        program = [prog for prog in programs.keys() if softwarename.lower() in programs[prog]]
        if len(program)>0:
            software[program[0]].append(user)

# ==============================================================================
# print to file
# ==============================================================================

# toprint is the string that will be written to people.rst
# write header
toprint = '.. _page-people:\n\n#############\nCluster users\n#############\n'

# add disclaimer
toprint += '''
.. topic:: Help wanted

  Not listed? Are you missing a user? Is something incorrect or outdated?

  Please contact: MaTeCluster@tue.nl

.. contents::
  :local:
  :depth: 3
  :backlinks: top

'''

# find the print format, as a function of the content with
# add 2 to make the formatting by Sphinx more pretty
fmt    = ''
dashes = ''

for key in what:
  l       = max([max([len(users[i][key]) for i in users]),len(key)])+2
  fmt    += '%-'+str(l)+'s '
  dashes += '='*l+' '

dashes += '\n'
fmt    += '\n'


##########################################
##### USER OVERVIEW SORTED BY USER
toprint += 'User overview\n-------------\n\n'

# table of users
toprint += dashes
# what
toprint += fmt % tuple(what)
toprint += dashes
# users
for user in sorted(users.keys()):
  toprint += fmt % tuple([users[user][field] for field in what])

toprint += dashes
##########################################

##########################################
##### PROGRAM OVERVIEW LISTING ALL USERS
for program in progsort:
  if program in software:
    # only print if userlist in this particular program is not empty
    if len(software[program])>0:
      toprint += '\n\n'+program+'\n'+len(program)*'-'+'\n\n'+dashes
      # what
      toprint += fmt % tuple(what)
      toprint += dashes
      for user in sorted(software[program]):
        toprint += fmt % tuple([users[user][field] for field in what])
      toprint += dashes


##########################################
# write the final string
open('people.rst','w').write(toprint)
#######################
