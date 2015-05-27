
import os,sys

text = '''
The following input file is specified:

  $ %s

The absolute path of this file is:

  $ %s

This script runs in:

  $ %s

''' % (
  sys.argv[0],
  os.path.abspath(sys.argv[0]),
  os.getcwd()
)

open('output.txt','w').write(text)