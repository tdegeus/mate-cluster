'''
Description
===========

The ``gpbs``-module is used to read/store/write information from the PBS-queuing
system. In particular it reads/convert the output of (either of) the following
commands::

  qstat -f    # information on individual jobs
  pbsnodes    # information on the status of the compute-nodes
  ganglia ... # information on the status of the compute-nodes

Main usage
==========

1.  Read individual job information::

      jobs = gpbs.qstatRead()

    This command reads the information from the ``qstat -f`` command and stores
    it as a list of individual jobs [dict].

2.  Read basic compute-node information::

      nodes = gpbs.pbsRead(ganglia=False)

    This command reads the information from the ``pbsnodes`` command and stores
    it as a list of individual compute-nodes [dict].

3.  Read detailed compute-node information::

      nodes = gpbs.pbsRead()

    This command reads the information from the ``pbsnodes`` and
    ``ganlia ...`` command and stores it as a list of individual compute-nodes
    [dict]. Notice: the ganglia command is slow, as it needs to connect to each
    of the individual nodes.

Implementation details
======================

Basic interface
---------------

The basic interface with the module is through:

1. The information is read by one of the following commands::

     jobs  = gpbs.qstatRead()
     nodes = gpbs.pbsRead()

   These commands return: a list of jobs/nodes, with a dictionary per
   list-entry. Each entry in the dictionary has at least the following methods::

     __cmp__(self,other)  # to compare (e.g. sort) the list
     __str__(self)        # to convert the entry to a string

   To deal with the custom classes (see below) and "None" entries when the
   "qstat -f" and/or "pbsnodes" command did not posses some of the data, the
   "Data"-class is used. It acts as the Swiss-army knife of the "gpbs"-module:

   * Perform arithmetic operations (e.g. "__cmp__" to sort) even when
     "None"-entries are encountered.
   * Convert fields to humanly-readable strings (e.g. walltime="1m" or
     host="1*").
   * Compare based on string input (e.g. check if walltime ">1d".

2. Calculate additional summary information::

     qsum = gpbs.qstatSummary(jobs,nodes)
     psum = gpbs.pbsSummary(nodes)

   The ouput is again a list of jobs/nodes/owners/... where each list-entry is
   a dictionary. Similar to above, each entry in the dictionary has at least
   the following fields:

     __cmp__(self,other)  # to compare (e.g. sort) the list
     __str__(self)        # to convert the entry to a string

Classes
-------

**Byte(float)**

  Class to convert bytes (as "floats") to/from humanly readable strings, e.g.

    1mb <-> 1.0e6

  This class is a child of the "float"-class and therefore all it's methods are
  inherited by this class. Overwritten/extra methods:
  * __repr__() and __str__(): called by e.g. "print" and "str(...)".
  * strcmp(expr): compare a humanly readable string.

**Time(float)**

  Class to convert seconds (as "floats") to/from humanly readable strings, e.g.

    2m <-> 60.0

  This class is a child of the "float"-class and therefore all it's methods are
  inherited by this class. Overwritten/extra methods:
  * __repr__() and __str__(): called by e.g. "print" and "str(...)".
  * strcmp(expr): compare a humanly readable string.

**ResNode**

  CPU resources requested for the job. Fields:

  * nnode:  #nodes
  * npcu:   #CPUs per node
  * ctype:  CPU type

  To convert to string (e.g. "1:2:i") use str(...).

**Host**

  Compute-node information for the job. Fields:

  * node:   compute-node-number
  * cpu:    CPU number
  * ctype:  CPU type
  * ntype:  totals per ctype

  To convert to string (e.g. "10*") use str(...).

To-do list:
-----------

* Update qstatLog / pbsLog (?), also change to "ascii" in-stead of binary
  to make more readable.

Change-log
----------

Version 1.3 - June 2014 - [TdG]

* Introduced the "Data" class as Swiss army knife handle all information fields.
  The Data class is to store/write all the Job/Node fields. This class also
  deals with "None" fields that are encountered if the data was not read.

Version 1.2 - May 2014 - [TdG]

* Numerous changes to accommodate myqstat better.
* Removed "HostInfo": qstatLog should be changed accordingly.

Version 1.1 - January 2014 - [JvB,TdG]

* Small bug-fixes [TdG].
* Added CPU-type to Host [TdG].
* Add log-commands (qstatLog,pbsLog) used for logging [JvB,TdG].

Version 1.0 - January 2014 - [TdG]

* First version.

Copyright
---------

[TdG]   T.W.J. de Geus
        t.degeus@gmail.com
        www.geus.me

[JvB]   J. van Beeck
        j.v.beeck@tue.nl
'''

# ==============================================================================
# reserved nodes
# ==============================================================================

class ResNode:
  '''
Description
-----------

CPU-resources reserved for a job:

======= ===============================
field   description
======= ===============================
nnode   #nodes
------- -------------------------------
ncpu    #CPUs
------- -------------------------------
ctype   CPU type (e.g. intel,amd)
======= ===============================

Input arguments (1/2)
---------------------

**string** = ``<str>``

  String of the format "1:ppn=2:intel" whereby the owner of this job has
  requested 2 CPUs on 1 node of type "intel".

Input arguments (2/2)
---------------------

**nnode** = ``<int>``

  Number of nodes.

**ncpu** = ``<int>``

  Number of CPUs.

**ctype** = ``<str>``

  Type of processor.

Usage
-----

* Store data or convert string::

    gpbs.ResNodes(nnode=...,ncpu=...,ctype=...)
    # or
    gpbs.ResNodes(string="1:ppn=1:intel")

* Compare::

    # set a variable "A"
    A = gpbs.ResNodes(...)

    # compare number of CPUs: compare to "ResNodes"-class
    A > gpbs.ResNodes(...)

    # compare number of CPUs: compare to string
    A > "10"

* Convert to humanly readable string::

    A = gpbs.ResNodes(...)

    print A # str(A)

      "1:1:i"

* Convert to PBS-options::

    A = gpbs.ResNodes(...)

    print A.pbsopt()

      "nodes=1:ppn=1:intel"
  '''

  # ----------------------------------------------------------------------------
  # class initiator
  # ----------------------------------------------------------------------------

  def __init__(self,**kwargs):

    # set defaults
    for key in ['nnode','ncpu','ctype']:
      if key in kwargs:
        setattr(self,key,kwargs[key])
      else:
        setattr(self,key,None)

    # read string
    if 'string' in kwargs:

      # check for other arguments
      if len(kwargs)>1:
        raise IOError('If "string" supplied: supply nothing else')

      # alias to variable
      string = kwargs['string']

      # convert string: type 1 (?)
      if len(string.split('ppn='))==1:
        self.nnode = 1
        self.ncpu  = 1
        for ctype in ['intel','amd']:
          if len(string.split(ctype))>1:
            self.ctype = ctype
      # convert string: type 2 (?)
      else:
        # split using format: NNODE:ppn=NCPU:CTYPE
        string = (string.replace('ppn=','')+':'*3).split(':')[0:3]
        # number of nodes
        try:
          self.nnode = int(string[0])
        except:
          pass
        # number of CPUs
        try:
          self.ncpu  = int(string[1])
        except:
          pass
        # type
        if len(string[2])>0:
          self.ctype = string[2]
        else:
          self.ctype = 'other'

  # ----------------------------------------------------------------------------
  # compare: "<" "<=" "==" ">=" ">"
  # ----------------------------------------------------------------------------

  def __cmp__(self,other):

    # set comparison depending on type of "other"
    if isinstance(other,ResNode):
      A = self.ncpu
      B = other.ncpu
    elif type(other)==str:
      A = str(self.ncpu)
      B = other
    elif type(other)==int:
      A = self.ncpu
      B = other
    else:
      return +1

    # compare "A" and "B"
    if A<B:
      return -1
    elif A>B:
      return 1
    else:
      return 0

  # ----------------------------------------------------------------------------
  # write humanly readable output, and create alias for print command
  # ----------------------------------------------------------------------------

  def __repr__(self):
    return self.write()
  def __str__(self):
    return self.write()

  def write(self):
    '''
Convert to human readable string, of the format "1:2:i". For this example the
owner has requested 1 node, 2 CPUs, of the intel class.
    '''
    txt = ''
    if self.nnode>0:
      txt += str(self.nnode)
    txt += ':'
    if self.ncpu>0:
      txt += str(self.ncpu)
    txt += ':'
    if self.ctype not in ['other'] and self.ctype is not None:
      txt += self.ctype[0]
    return txt

  # ----------------------------------------------------------------------------
  # return to PBS options
  # ----------------------------------------------------------------------------

  def pbsopt(self):
    '''
Write as PBS-string
    '''

    text = []

    if self.nnode is not None:
      text.append('nodes=%d'%self.nnode)
    if self.ncpu is not None:
      text.append('ppn=%d'%self.ncpu)
    if self.ctype is not None:
      text.append(self.ctype)

    return ':'.join(text)

# ==============================================================================
# information of the compute-node
# ==============================================================================

class Host:
  '''
Description
-----------

Class to store host information, and print is in an easily readable format.

===== ============================================================
field description
===== ============================================================
node  list with node-numbers
----- ------------------------------------------------------------
cpu   list with CPU-numbers on the corresponding node
----- ------------------------------------------------------------
ctype CPU-type per node/CPU
      (only after "typecal")
----- ------------------------------------------------------------
ntype dictionary with total number of nodes per unique "ctype"
      (only after "typecal")
===== ============================================================

Input arguments (1/2)
---------------------

**string** = ``<str>``

  String in the following format: "compute-0-1/12+compute-0-1/1".

Input arguments (1/2)
---------------------

**node** = ``<lst>``

  List with node numbers.

**cpu** = ``<lst>``

  List with CPU numbers.

Usage
-----

* Store data or convert string::

    gpbs.Host(node=[...],cpu=[...])
    # or
    gpbs.Host(string="...")

* Compare::

    # set a variable "A"
    A = gpbs.Host(...)

    # compare (first) node-number: to "Host"-class
    A > gpbs.Host(...)

    # compare (first) node-number as string: to string
    A > "10"

    # 'advanced' string compare
    A.strcmp(">10")

* Write humanly readable output (e.g. "1" or "1*").

  '''

  # ----------------------------------------------------------------------------
  # class initiator
  # ----------------------------------------------------------------------------

  def __init__(self,string=None,node=[],cpu=[]):

    # initiate
    self.node = node
    self.cpu  = cpu
    self.ncpu = 0
    # convert/store string
    if string is not None:
      # remove the "compute-0-" and split at "+"
      string = string.replace("compute-0-","").split("+")
      # store nodes and CPU
      self.node = [int(i.split("/")[0]) for i in string]
      self.cpu  = [int(i.split("/")[1]) for i in string]
      # calculate counters
      self.ncpu = len(self.cpu)

  # ----------------------------------------------------------------------------
  # compare: "<" "<=" "==" ">=" ">"
  # ----------------------------------------------------------------------------

  def __cmp__(self,other):
    '''
Comparison for operators "<" "<=" "==" ">=" ">". Comparison to:

* Host
* str
    '''

    # set comparison depending on type of "other"
    if isinstance(other,Host):
      A = self.node[0]
      B = other.node[0]
    elif type(other)==str:
      A = self.node.write()
      B = other
    else:
      return +1

    # compare "A" and "B"
    if A<B:
      return -1
    elif A>B:
      return 1
    else:
      return 0

  # ----------------------------------------------------------------------------
  # add hosts
  #TODO: deepcopy
  # ----------------------------------------------------------------------------

  def __add__(self,other):

    # check the class of other
    if not isinstance(other,Host):
      raise IOError('"other" must be of the Host class')

    # add fields
    self.node += other.node
    self.cpu  += other.cpu
    self.ncpu += other.ncpu

    return self

  # ----------------------------------------------------------------------------
  # return #CPU as integer
  # ----------------------------------------------------------------------------

  def __int__(self):
    return self.ncpu

  # ----------------------------------------------------------------------------
  # write humanly readable output, and create alias for print command
  # ----------------------------------------------------------------------------

  def __repr__(self):
    return self.write()
  def __str__(self):
    return self.write()

  def write(self):
    '''
Create human readable output. E.g.::

  node = [1,1,1,1]  --> "1"
  node = [1,1,1,2]  --> "1*"
    '''
    node = self.node
    if self.ncpu > 0:
      if node.count(node[0])==len(node):
        return "%d" % node[0]
      else:
        return "%d%s" % (node[0],"*")
    else:
      return ''

  # ----------------------------------------------------------------------------
  # compare humanly readable string
  # ----------------------------------------------------------------------------

  def strcmp(self,expr):
    '''
Compare time to humanly readable string, e.g.::

  x.strcmp(">10")
  x.strcmp("<=10")
  x.strcmp("10")
    '''

    try:
      if expr[:2]=='<=':
        return any([i for i in self.node if i<=int(expr[2:])])
      elif expr[:2]=='>=':
        return any([i for i in self.node if i>=int(expr[2:])])
      elif expr[:2]=='==':
        return any([i for i in self.node if i==int(expr[2:])])
      elif expr[0]=='<':
        return any([i for i in self.node if i< int(expr[1:])])
      elif expr[0]=='>':
        return any([i for i in self.node if i> int(expr[1:])])
      else:
        return any([i for i in self.node if i==int(expr)    ])
    except:
      return False

  # ----------------------------------------------------------------------------
  # convert nodes to CPU-type
  # ----------------------------------------------------------------------------

  def typecal(self,nodes):
    '''
Description
-----------

Calculate the CPU type of each node. An additional field "ctype" is added to
class, which is a list of CPU-types. For example::

  self.node  = [   11    ,   11    ]
  self.ctype = [ 'intel' , 'intel' ]

Input arguments
---------------

**nodes**

  List with node-information (see pbsRead).
    '''

    # set allowed CPU-type
    types = ['intel','amd']
    # check allowed CPU-type
    for node in nodes:
      if str(node['ctype']) not in types:
        raise IOError('Unknown CPU-type %s',node.ctype)

    # convert list of nodes to type per node
    clist = {}
    for node in nodes:
      clist[int(node['node'])] = str(node['ctype'])

    # convert node list to type list
    self.ctype = [clist[i] for i in self.node]

    # calculate total
    self.ntype = {}
    for t in types:
      self.ntype[t] = self.ctype.count(t)

    # calculate overall total
    self.ntype['total'] = sum([self.ntype[i] for i in self.ntype])

    return self

# ==============================================================================
# memory
# ==============================================================================

class Byte(float):
  '''
Description
-----------

Class to store (byte-)data, and print is in an easily readable format.

Input arguments (mutually exclusive)
------------------------------------

**num** = ``<float>``

  Number of seconds.

**string** = ``<str>``

  String in the following format: "1gb".

Function overview
-----------------

**write**

  Write humanly readable output (e.g. "1mb").

**strcmp**

  Compare a humanly readable string (e.g. ">10mb").
  '''

  # ----------------------------------------------------------------------------
  # class initiator
  # ----------------------------------------------------------------------------

  def __new__(cls,num=None,string=None):
    '''
Initiate variables. Notice "__new__" instead of "__init__" as the Python-class
"float" is overloaded. For this class "__init__" is non-writable.
    '''

    # convert "1gb" to float
    def convertstring(string):
      # set conversion ratio
      ratio = {}
      ratio["tb"] = 1.0e12
      ratio["gb"] = 1.0e9
      ratio["mb"] = 1.0e6
      ratio["kb"] = 1.0e3
      # loop to find conversion
      for (i,iden) in enumerate(ratio):
        if len(string.split(iden))>1:
          return float(string.split(iden)[0])*ratio[iden]
        if i==len(ratio):
          iden = 'b'
          if len(string.split(iden))>1:
            return float(string.split(iden)[0])*ratio[iden]
          else:
            raise IOError('Unknown "human" data %s'%string)

    # check number of arguments
    arg = [True for i in [num,string] if i is not None]
    if len(arg)==0:
      return None
    elif len(arg)!=1:
      raise IOError('Incorrect number of input options')
    # convert string to number
    if string is not None:
      num = convertstring(string)

    # initiate as float
    return float.__new__(cls,float(num))

  # ----------------------------------------------------------------------------
  # write humanly readable output, and create alias for print command
  # ----------------------------------------------------------------------------

  def __repr__(self):
    return self.write()
  def __str__(self):
    return self.write()

  def write(self,precision=None):
    '''
Create human readable output. E.g.::

  1000.0 == "1mb"
    '''
    # set conversion factors (days,hours,minutes,seconds)
    ratio = {}
    ratio[1.0e12] = 'tb'
    ratio[1.0e9]  = 'gb'
    ratio[1.0e6]  = 'mb'
    ratio[1.0e3]  = 'kb'
    ratio[1.0e0]  = 'b'
    for fac in sorted(ratio)[-1::-1]:
      if self>=fac:
        # set precision default
        if precision is None:
          precision = 0
        # return output
        return ('%1.'+str(precision)+'f'+ratio[fac])%(self/fac)

    return '0.0b'

  # ----------------------------------------------------------------------------
  # compare humanly readable string
  # ----------------------------------------------------------------------------

  def strcmp(self,expr):
    '''
Compare time to humanly readable string, e.g.::

  x.strcmp(">10mb")
  x.strcmp("<=10mb")
  x.strcmp("10mb")
      '''

    try:
      if expr[:2]=='<=':
        return self <= Byte(human=expr[2:])
      elif expr[:2]=='>=':
        return self >= Byte(human=expr[2:])
      elif expr[:2]=='==':
        return self == Byte(human=expr[2:])
      elif expr[0]=='<':
        return self  < Byte(human=expr[1:])
      elif expr[0]=='>':
        return self  > Byte(human=expr[1:])
      else:
        return self == Byte(human=expr)
    except:
      return False

# ==============================================================================
# time
# ==============================================================================

class Time(float):
  '''
Description
-----------

Class to store time, and print is in an easily readable format.

Input arguments (mutually exclusive)
------------------------------------

**num** = ``<float>``

  Number of seconds.

**string** = ``<str>``

  String in the following format: "HH:MM:SS".

**human** = ``<str>``

  Time in humanly readable format, e.g. "1d".

Function overview
-----------------

**write**

  Write humanly readable output (e.g. "2d").

**strcmp**

  Compare a humanly readable string (e.g. ">10s").
  '''

  # ----------------------------------------------------------------------------
  # class initiator
  # ----------------------------------------------------------------------------

  def __new__(cls,num=None,string=None,human=None):
    '''
Initiate variables. Notice "__new__" instead of "__init__" as the Python-class
"float" is overloaded. For this class "__init__" is non-writable.
    '''

    # convert "HH:MM:SS" to float
    def convertstring(string):
      string = string.split(":")
      return float(int(string[0])*60*60+int(string[1])*60+int(string[2]))

    # convert "1d" to float
    def converthuman(string):
      # set conversion ratio
      ratio = {}
      ratio["d"] = 60.0*60.0*24.0
      ratio["h"] = 60.0*60.0
      ratio["m"] = 60.0
      ratio["s"] = 1.0
      # loop to find conversion
      for (i,iden) in enumerate(ratio):
        if len(string.split(iden))>1:
          return float(string.split(iden)[0])*ratio[iden]
        if i==len(ratio):
          raise IOError('Unknown "human" time %s'%string)

    # check number of arguments
    arg = [True for i in [num,string,human] if i is not None]
    if len(arg)==0:
      return None
    elif len(arg)!=1:
      raise IOError('Incorrect number of input options')
    # convert string to number
    if string is not None:
      num = convertstring(string)
    if human is not None:
      num = converthuman(human)

    # initiate as float
    return float.__new__(cls,float(num))

  # ----------------------------------------------------------------------------
  # write humanly readable output, and create alias for print command
  # ----------------------------------------------------------------------------

  def __repr__(self):
    return self.write()
  def __str__(self):
    return self.write()

  def write(self,precision=None):
    '''
Create human readable output. E.g.::

  24*60*60 == "1.0d"
    '''
    # set conversion factors (days,hours,minutes,seconds)
    ratio = {}
    ratio[60.0*60.0*24.0] = 'd'
    ratio[60.0*60.0]      = 'h'
    ratio[60.0]           = 'm'
    ratio[1.0]            = 's'
    for fac in sorted(ratio)[-1::-1]:
      if self>=fac:
        # set precision default, based on scaled output
        if precision is None:
          if self/fac>=2:
            precision = 0
          else:
            precision = 1
        # return output
        return ('%1.'+str(precision)+'f'+ratio[fac])%(self/fac)

    return '0.0s'

  # ----------------------------------------------------------------------------
  # compare humanly readable string
  # ----------------------------------------------------------------------------

  def strcmp(self,expr):
    '''
Compare time to humanly readable string, e.g.::

  x.strcmp(">10m")
  x.strcmp("<=10d")
  x.strcmp("10d")
    '''

    try:
      if expr[:2]=='<=':
        return self <= Time(human=expr[2:])
      elif expr[:2]=='>=':
        return self >= Time(human=expr[2:])
      elif expr[:2]=='==':
        return self == Time(human=expr[2:])
      elif expr[0]=='<':
        return self  < Time(human=expr[1:])
      elif expr[0]=='>':
        return self  > Time(human=expr[1:])
      else:
        return self == Time(human=expr)
    except:
      return False


# ==============================================================================
# support function to split text
# ==============================================================================

def csplit(text,name,postfix=' =',sep='\n',dtype=None):
  '''
Split a string, and convert to a specific data type.

Input arguments
---------------

**text** <str>

  String to split/convert.

**name** <str>

  Key-name, at which to split the string (in front of the data).

Input options
-------------

**postfix** <str>

  Post-fix of the key-name (in front of the data).

**sep** <str>

  Separator (after the data).

**dtype** [None] | int | float | Byte | Time | ResNode | Host | ...

  Data-type to which to convert the data.

Output arguments
----------------

**data** [<str>] | ...

  Data read (and converted to a specific data-type).

Examples
--------

To read the memory form the following string::

  ...
  resources_used.cputime = 995:58:01
  resources_used.mem     = 6286932kb
  resources_used.vmem    = 6611296kb
  ...

use the command::

  csplit(txt,'resources_used.mem',dtype='Data')
  '''

  # split the text
  try:
    text = text.split(name+postfix)[1].split(sep)[0].strip()
  except:
    return None
  # convert the data-type
  if dtype in ['Byte','ResNode','Time','Host']:
    return eval('%s(string=text)'%dtype)
  elif dtype is not None:
    return eval('%s(text)'%dtype)
  else:
    return text

# ==============================================================================
# data entry
# ==============================================================================

class Data:
  '''
Description
-----------

This class serves as a Swiss-army knife for all fields in Job and Node. This
class is used to:

* Distinguish between unread (None) and read items.

* Compare strings, etc.

* Convert field to printable string (by str(...)).

Input arguments
---------------

**data**

  The actual data. Can be "float", "int", "Byte", "Time, or any other class.

**fmt**

  The print format of this field, e.g. "%s" or "%4.2f". If "self.data" is
  not read (==None) the output is an empty string.

**dtype**

  The type the the "data".
  '''

  # ----------------------------------------------------------------------------
  # class initiator
  # ----------------------------------------------------------------------------

  def __init__(self,data=None,fmt='%s',dtype=None):
    self.data  = data
    self.fmt   = fmt
    self.dtype = dtype

  # ----------------------------------------------------------------------------
  # compare Data to other variable (<,<=,==,>=,>)
  # ----------------------------------------------------------------------------

  def __cmp__(self,other):
    '''
Compare "self" to another field. Depending on the class of "other"

* ``Data``::

    return self.other ? other.data

  No safe-guard needed for None items, automatically taken care of.

* ``str``::

    re.match: self.data ? other

* ``Time`` | ``Byte``::

    self.data.strcmp ? other
    '''

    # self.data(None) ? Data|None
    if self.data is None:

      # self.data(None) == other.Data(None)
      if isinstance(other,Data):
        if other.data is None:
          return 0

      # self.data(None) == None
      if other is None:
        return 0

      # all other cases
      return -1

    # Data ? Data
    if isinstance(other,Data):

      if self.data<other.data:
        return -1
      elif self.data>other.data:
        return 1
      else:
        return 0

    # Data ? str
    # self.dtype(Time|Byte):  strcmp (e.g. Time(14.).strcmp("<10d")
    # other cases:            regexp (e.g. ^.*$)
    if type(other)==str:

      if self.dtype in ['Time','Byte','Host']:
        if self.data.strcmp(other):
          return 0

      if self.dtype=='str' or self.dtype=='int':
        import re
        if re.compile(other).match(str(self.data)):
          return 0

      return -1

    # all other comparison, let the classes figure out what to do
    if self.data < other:
      return -1
    elif self.data > other:
      return 1
    else:
      return 0

  # ----------------------------------------------------------------------------
  # return as different data type
  # ----------------------------------------------------------------------------

  def __int__(self):
    try:
      return int(self.data)
    except:
      return 0

  def __float__(self):
    try:
      return float(self.data)
    except:
      return 0.0

  def __len__(self):
    return len(self.data)

  # ----------------------------------------------------------------------------
  # mathematical operations
  # ----------------------------------------------------------------------------

  # front-end of "arithmetic"
  # -------------------------

  def __add__(self,other):
    return self.arithmetic(other,'+')

  def __sub__(self,other):
    return self.arithmetic(other,'-')

  def __mul__(self,other):
    return self.arithmetic(other,'*')

  def __div__(self,other):
    return self.arithmetic(other,'/')

  # actual operation
  # ----------------

  def arithmetic(self,other,operator):

    # copy the input to a new output variable
    # this is needed to make sure that that operation does not influence the
    # variables. E.g. in "A = B+C" the variable "B" and "C" must be unaffected
    import copy
    result = copy.deepcopy(self)

    # operator between "Data" and "Data" objects
    if isinstance(other,Data):
      # both not None
      # normal arithmetic
      if self.data is not None and other.data is not None:
        if operator=='+':
          result.data = self.data+other.data
        elif operator=='-':
          result.data = self.data-other.data
        elif operator=='*':
          result.data = self.data*other.data
        elif operator=='/':
          result.data = self.data/other.data
      # other.data == None
      # return self
      elif self.data is not None:
        pass
      # self.data == None
      # return other
      else:
        result.data = other.data

      # convert output type
      if self.dtype=='Byte' and other.dtype=='Byte':
        result.data = Byte(result.data)
      if self.dtype=='Time' and other.dtype=='Time':
        result.data = Time(result.data)

    # operator between "Data" and some other object
    else:
      if operator=='+':
        result = self.data+other
      elif operator=='-':
        result = self.data-other
      elif operator=='*':
        result = self.data*other
      elif operator=='/':
        result = self.data/other

    return result

  # ----------------------------------------------------------------------------
  # convert to string (e.g. "print" or "str" commands)
  # ----------------------------------------------------------------------------

  def __str__(self):
    return self.__repr__()

  def __repr__(self):
    if self.data is None:
      return ''
    else:
      return self.fmt % self.data

  # ----------------------------------------------------------------------------
  # return as original class (return self.data)
  # ----------------------------------------------------------------------------

  def type(self):
    '''
Return the "data".
    '''
    return self.data

# ==============================================================================
# convert `qstat -f` output
# ==============================================================================

def qstatRead(qstat=None):
  '''
Description
-----------

Read the output of the `qstat -f` command. The output is converted to a list of
jobs. Each job is a dictionary with fields:

=========== ======================================================
key         description
=========== ======================================================
id          unique job-identifier
owner       job-owner
name        job-name
resnode     reserved CPU resources (e.g. "1:1:i")
state       job-state ("Q" or "R")
host        compute-node(s) at which the job is running
pmem        requested memory
memused     current memory usage
walltime    time the the job has been running
cputime     effective time that CPU(s) have been in use
score       cputime / ( walltime * ncpu )
=========== ======================================================

Input options
-------------

**qstat** [None] | <str>

  In stead of reading the `qstat -f` command, supply a string containing this
  output. Mostly used for debugging.

Returns
-------

**jobs** <lst>

  A list with jobs.
  '''

  # convert job to dictionary
  def convert(qstat):
    # initiate output
    d = {}
    # convert str -> fields
    d['id'      ] = Data(int(qstat.split('\n')[0].split('.')[0].strip())        ,'%d','int'    )
    d['name'    ] = Data(csplit(qstat,'Job_Name' )                              ,'%s','str'    )
    d['owner'   ] = Data(csplit(qstat,'Job_Owner').split('@')[0]                ,'%s','str'    )
    d['state'   ] = Data(csplit(qstat,'job_state')                              ,'%s','str'    )
    d['resnode' ] = Data(csplit(qstat,'Resource_List.nodes'    ,dtype='ResNode'),'%s','ResNode')
    d['pmem'    ] = Data(csplit(qstat,'Resource_List.pmem'     ,dtype='Byte'   ),'%s','Byte'   )
    d['memused' ] = Data(csplit(qstat,'resources_used.mem'     ,dtype='Byte'   ),'%s','Byte'   )
    d['cputime' ] = Data(csplit(qstat,'resources_used.cput'    ,dtype='Time'   ),'%s','Time'   )
    d['walltime'] = Data(csplit(qstat,'resources_used.walltime',dtype='Time'   ),'%s','Time'   )
    d['host'    ] = Data(csplit(qstat,'exec_host'              ,dtype='Host'   ),'%s','Host'   )
    # calculate score
    try:
      walltime   = float(    d['walltime'] )
      cputime    = float(    d['cputime' ] )
      ncpu       = float(int(d['host'    ]))
      d['score'] = Data(cputime/(walltime*ncpu),'%4.2f','float')
      d['ncpu' ] = Data(ncpu,'%d','int')
    except:
      d['score'] = Data()
      d['ncpu' ] = Data()
    # close
    return d

  # read output `qstat -f` command
  if qstat is None:
    import commands
    qstat = commands.getoutput('qstat -f')

  # replace hard word-wrap, and split in jobs
  jobs = qstat.replace('\n\t','')
  jobs = jobs.split('Job Id:')[1:]
  # read/convert each job
  for (ijob,job) in enumerate(jobs):
    jobs[ijob] = convert(job)

  return jobs

# ==============================================================================
# compute node information
# ==============================================================================

def pbsRead(pbsnodes=None,ganglia=None):
  '''
Description
-----------

Read the output of the `pbsnodes` and the `ganglia` command. The output is
converted to a list of compute-nodes. Each node is a dictionary with the
following fields:

=========== =======================================================
key         description
=========== =======================================================
name        name of the compute-node
state       state (e.g. "free", "job-exclusive", "down", etc.)
ncpu        #CPUs
cpufree     #CPUs free
ctype       type of the CPUs
jobs        job-id of the jobs running on the node
njobs       #jobs running on the node
load        load of the node, scaled by the number of CPUs in use
memt        total memory
memp        physical memory
mema        available memory
memu        used memory
memr        fraction of the memory used
disk_total  total disk space
disk_free   free disk space
disk_used   used disk space
disk_rel    fractions of the disk space used
bytes_in    network traffic inbound
bytes_out   network traffic outbound
bytes_tot   total network traffic
cpu_idle    CPU idle time
=========== =======================================================

Input option
------------

**pbsnodes** [None] | <str>

  In stead of reading the `pbsnodes` command, supply a string containing this
  output. Mostly used for debugging.

**ganglia** [None] | False | <str>

  If set ``False`` the `ganglia` command is not read. This option is used to
  speed up, as the `ganglia` command is slow. If a <str> is supplied the
  `ganglia` command is also not read, but the output in the <str> is used in
  stead. Notice that the following command should be used to form the string::

    ganglia disk_total disk_free bytes_in bytes_out cpu_idle

Returns
-------

**nodes** <lst>

  A list with compute-nodes.
  '''

  # read `pbsnodes` command
  # -----------------------

  # read the `pbsnodes` command
  if pbsnodes is None:
    import commands
    pbsnodes = commands.getoutput('pbsnodes')
  # split the `pbsnodes` output in different nodes
  nodes = filter(None,pbsnodes.split('\n\n'))

  # read `ganglia` command, convert to dictionary
  # ---------------------------------------------

  # initiate the ganglia options, and the output
  args = ['disk_total','disk_free','bytes_in','bytes_out','cpu_idle']
  dat  = {}
  # read the `ganglia` command
  if ganglia is None:
    import commands
    ganglia = commands.getoutput('ganglia '+' '.join(args))
  # convert the `ganglia` command output to dictionary
  if ganglia is not False:
    # loop over lines: split lines and store in dictionary per node
    for line in ganglia.split('\n')[:-1]:
      out = filter(None,line.replace("\t","").split(" "))
      (name,out) = (out[0],out[1:])
      dat[name] = {arg:out[i] for (i,arg) in enumerate(args)}
  # change name
  ganglia = dat
  # change the units of the ganglia command / convert to Data-type
  for node in ganglia:
    for key in ganglia[node]:
      if key in ['disk_total','disk_free']:
        ganglia[node][key] = Data(Byte(float(ganglia[node][key])*1.0e9),'%s'   ,'Byte')
      elif key in ['bytes_in','bytes_out']:
        ganglia[node][key] = Data(Byte(float(ganglia[node][key])      ),'%s'   ,'Byte')
      else:
        ganglia[node][key] = Data(     float(ganglia[node][key])       ,'%4.2f','float')

  # convert `pbsnodes` command to dictionary (and include defaults)
  # ---------------------------------------------------------------

  # support function, split jobs: 0/XXX.hostname
  def splitjobs(txt):
    try:
      jobs = txt.split('jobs =')[1].split('\n')[0].strip().split(',')
      return [int(i.split('/')[1].split('.')[0].strip()) for i in jobs]
    except:
      return None

  # convert string to dictionary
  def convert(text):
    d = {}
    d['name' ] = Data(text.split('\n')[0]                                      ,'%s'   ,'str'  )
    d['state'] = Data(csplit(text,'state')                                     ,'%s'   ,'str'  )
    d['ncpu' ] = Data(csplit(text,'np',dtype='int')                            ,'%d'   ,'int'  )
    d['ctype'] = Data(csplit(text,'properties')                                ,'%s'   ,'str'  )
    d['jobs' ] = Data(splitjobs(text)                                          ,'%s'   ,'list' )
    d['load' ] = Data(csplit(text,'loadave' ,postfix='=',sep=',',dtype='float'),'%4.2f','float')
    d['memt' ] = Data(csplit(text,'totmem'  ,postfix='=',sep=',',dtype='Byte' ),'%s'   ,'Byte' )
    d['memp' ] = Data(csplit(text,'physmem' ,postfix='=',sep=',',dtype='Byte' ),'%s'   ,'Byte' )
    d['mema' ] = Data(csplit(text,'availmem',postfix='=',sep=',',dtype='Byte' ),'%s'   ,'Byte' )
    return d

  # loop over nodes and convert the string
  for (inode,node) in enumerate(nodes):
    # convert pbsnodes output
    n    = int(node.split('\n')[0].replace('compute-0-',''))
    node = convert(node)
    node['node'] = Data(n,'%d','int')
    name = str(node['name'])
    # add ganglia output
    for key in args:
      node[key] = Data()
    if name in ganglia:
      for key in ganglia[name]:
        node[key] = ganglia[name][key]
    # number of jobs
    try:
      node['njobs'] = Data(len(node['jobs']),'%d','int')
    except:
      node['njobs'] = Data()
    # number of CPUs free
    try:
      node['cpufree'] = Data(node['ncpu']-node['njobs'],'%d','int')
    except:
      node['cpufree'] = Data()
    # scale the load
    try:
      node['load'] = Data(node['load']/float(node['njobs']),'%4.2f','float')
    except:
      pass
    # available memory
    try:
      node['memu'] = Data(Byte(node['memt']-node['mema']),'%s','Byte')
    except:
      node['memu'] = Data()
    # relative memory usages
    try:
      node['memr'] = Data(float(node['memu']/node['memt']),'%4.2f','float')
    except:
      node['memr'] = Data()
    # disk usage
    try:
      node['disk_used'] = Data(Byte(node['disk_total']-node['disk_free']),'%s','Byte')
    except:
      node['disk_used'] = Data()
    # relative disk usage
    try:
      node['disk_rel'] = Data(float(node['disk_used']/node['disk_total']),'%4.2f','float')
    except:
      node['disk_rel'] = Data()
    # total network traffic
    try:
      node['bytes_tot'] = Data(Byte(node['bytes_in']+node['bytes_out']),'%s','Byte')
    except:
      node['bytes_tot'] = Data()

    # remove output
    if node['state'] not in ['free','job-exclusive']:
      for key in ['load','njobs','cpufree','memu','memr','disk_free','bytes_in',\
                  'bytes_out','bytes_tot','disk_rel','disk_used']:
        node[key] = Data()

    # store to list
    nodes[inode] = node

  return nodes

# ==============================================================================
# calculate node summary
# ==============================================================================

def pbsSummary(nodes):
  '''
Summarize the compute-node information. The output has the following structure:

  out[key][field] = N

  keys   = ['total','offline','online','njobs','cpufree']
  fields = ['total','intel','amd']
  '''

  # set output keys, and field per key; states which count as "online"
  keys   = ['total','offline','online','njobs','cpufree']
  fields = ['total','intel','amd']
  on     = ['free','job-exclusive']

  # initiate output
  out = {}
  for key in keys:
    out[key] = {}
    for field in fields:
      out[key][field] = 0

  # loop over nodes, and add to the appropriate fields
  for node in nodes:

    ctype = str(node['ctype'])
    state = str(node['state'])

    # add to total
    out['total']['total'] += int(node['ncpu'])
    out['total'][ctype]   += int(node['ncpu'])

    # add to online/offline
    if state in on:
      out['online']['total'] += int(node['ncpu'])
      out['online'][ctype]   += int(node['ncpu'])
    else:
      out['offline']['total'] += int(node['ncpu'])
      out['offline'][ctype]   += int(node['ncpu'])

    # add to working
    if state in on:
      out['njobs']['total'] += int(node['njobs'])
      out['njobs'][ctype]   += int(node['njobs'])

    # add to free
    if state in on:
      out['cpufree']['total'] += int(node['cpufree'])
      out['cpufree'][ctype  ] += int(node['cpufree'])

  return out

# ==============================================================================
# summarize the jobs
# ==============================================================================

def qstatSummary(jobs,nodes,key='owner'):

  # initiate output
  out = {}

  # loop over jobs, and add relative fields
  for job in jobs:

    # get storage key
    if key in ['owner']:
      field = str(job['owner'])
    # zero-initiate fields
    if field not in out:
      out[field] = {}
      out[field]['host'    ] = Data(Host(node=[],cpu=[]),'%s','Host')
      out[field]['memused' ] = Data(Byte(0.0),'%s','Byte')
      out[field]['cputime' ] = Data(Time(0.0),'%s','Time')
      out[field]['walltime'] = Data(Time(0.0),'%s','Time')
      out[field]['owner'   ] = str(job['owner'])
    # add fields
    for name in ['walltime','cputime','memused','host']:
      out[field][name] += job[name]

  # calculate number of CPUs per type, and score
  for key in out:
    # get cpu-type
    host = out[key]['host'].type().typecal(nodes)
    for name in host.ntype:
      out[key][name] = host.ntype[name]
    # add score
    try:
      walltime   = float(out[key]['walltime'])
      cputime    = float(out[key]['cputime' ])
      ncpu       = float(int(host))
      out[key]['score'] = Data(cputime/(walltime*ncpu),'%4.2f','float')
    except:
      out[key]['score'] = Data()

  return [out[key] for key in sorted(out)]

#TODO:
## ==============================================================================
## write/convert qstat log files
## ==============================================================================
#
#def qstatLog(read=None,path='.'):
#  '''
#Description
#------------
#
#Write/convert log-files of the "qstat -f" output. The following files are
#written (or modified):
#
#1.  "jobhistory_YYYY_MM.log"
#
#    A monthly summary.
#
#2.  "jobcurrent.log"
#
#    A temporary file with the last logged jobs. The files are written to the
#    monthly summary when they are finished.
#
#Input options
#-------------
#
#**read** = [``None``] | ``<str>``
#
#  Set the file-name to read.
#
#**path** = [``None``] | ``<str>``
#
#  Set the path in which to write the files.
#  '''
#
#  import time,os,struct
#
#  ### convert, set defaults
#  def default(job,fields):
#    # initiate output
#    out = dict()
#    # loop over fields
#    for field in fields:
#      if field in ['id','walltime','cputime','memused']:
#        if eval('job.%s'%field) is None:
#          out[field] = 0
#        else:
#          out[field] = int(eval('job.%s'%field))
#      elif field in ['owner','hostinfo']:
#        if eval('job.%s'%field) is None:
#          out[field] = ''
#        else:
#          out[field] = str(eval('job.%s'%field))
#      else:
#        raise IOError('Unknown field %s'%field)
#    return out
#
#  ### convert a job to a binary "string"
#  def job2bin(job,fields,fmt):
#    info = [job[i] for i in fields]
#    return struct.pack(fmt,*info)
#
#  ### convert a binary "string" to a job
#  def bin2job(string,fields,fmt):
#    import re
#    expr = re.compile('^[a-zA-Z0-9\.]+$')
#    args = {}
#    for (field,data) in zip(fields,struct.unpack(fmt,string)):
#      if field in ['owner','hostinfo']:
#        data = ''.join([i for i in data if expr.match(i)])
#      if field in ['walltime']:
#        data = float(data)
#      args[field] = data
#    return Job(**args)
#
#  ### fields and print settings (including the length of the binary "string")
#  fields = ['id','owner','walltime','cputime','memused','hostinfo']
#  fmt    = 'Q15sQQQ15s'
#  fmtlen = struct.calcsize(fmt)
#
#  ### read log-file
#  if read is not None:
#
#    jobs = open(read,'r').read()
#    jobs = [jobs[i:i+fmtlen] for i in range(0,len(jobs),fmtlen) ]
#    return [bin2job(job,fields,fmt) for job in jobs]
#
#  ### write the log-files
#  else:
#
#    # set the filenames
#    t = time.localtime()
#    filetemp = 'jobcurrent.log'
#    filehist = 'jobhistory_%s.log' % ('%04i_%02i'%(t.tm_year,t.tm_mon))
#    filetemp = os.path.join(path,filetemp)
#    filehist = os.path.join(path,filehist)
#
#    # list the current jobs, store the id's, and convert to binary
#    running   = qstatRead()
#    running   = [default(job,fields) for job in running]
#    runningid = [job['id'] for job in running]
#    running   = [job2bin(job,fields,fmt) for job in running]
#
#    # convert the "temp"-file to list, and read the job id
#    try:
#      temp   = open(filetemp,'r').read()
#      temp   = [temp[i:i+fmtlen] for i in range(0,len(temp),fmtlen) ]
#      tempid = [struct.unpack(fmt,job)[0] for job in temp]
#    except:
#      temp   = []
#      tempid = []
#
#    # combine finished jobs
#    finished = []
#    for (jobid,job) in zip(tempid,temp):
#      if jobid not in runningid:
#        finished.append(job)
#    # write log and "temp" file
#    open(filehist,'a').write(''.join(finished))
#    open(filetemp,'w').write(''.join(running))
#
## ==============================================================================
## write/convert pbs-node log files
## ==============================================================================
#
#def pbsLog(path='.',read=None):
#
#  import time,struct
#
#  ### set default values
#  def default(node,field):
#    # initiate output
#    out = dict()
#    # loop over fields
#    for field in fields:
#      # set defaults
#      if field in ['ncpu','cpufree','memt','memu','disk_total','disk_free']:
#        if eval('node.%s'%field) is None:
#          out[field] = 0
#        else:
#          out[field] = int(eval('node.%s'%field))
#      elif field in ['name','state']:
#        if eval('node.%s'%field) is None:
#          out[field] = ''
#        else:
#          out[field] = str(eval('node.%s'%field))
#      else:
#        raise IOError('Unknown field %s'%field)
#      # scale to ganglia command
#      if field in ['disk_free','disk_total']:
#        out[field] /= 1.0e9
#    return out
#
#  ### convert a job to a binary "string"
#  def node2bin(node,fields,fmt):
#    info = [node[i] for i in fields]
#    return struct.pack(fmt,*info)
#
#  ### convert a binary "string" to a node
#  def bin2node(string,fields,fmt):
#    import re
#    expr = re.compile('^[a-zA-Z0-9\.]+$')
#    args = {}
#    for (field,data) in zip(fields,struct.unpack(fmt,string)):
#      if field in ['name','state']:
#        data = ''.join([i for i in data if expr.match(i)])
#      # fix custom fields
#      if field in ['name']:
#        data = data.replace('compute0','compute-0-')
#      if field in ['state']:
#        data = data.replace('jobexclusive','job-exclusive')
#      args[field] = data
#    return Node(**args)
#
#  ### basic parameters
#  fields = ['name','state','ncpu','cpufree','memt','memu','disk_total','disk_free']
#  fmt    = '15s15sQQQQQQ'
#  fmtlen = struct.calcsize(fmt)
#
#  ### read an archive
#  if read is not None:
#
#    nodes = open(read,'r').read()
#    nodes = [nodes[i:i+fmtlen] for i in range(0,len(nodes),fmtlen) ]
#    return [bin2node(node,fields,fmt) for node in nodes]
#
#  ### create an archive
#  else:
#
#    # set the filename
#    t = time.localtime()
#    filename = 'nodehistory_%04i%02i%02i_%02i%02i%02i.log'%(t.tm_year,t.tm_mon,t.tm_mday,t.tm_hour,t.tm_min,t.tm_sec)
#
#    # get node information
#    nodes = pbsRead()
#    nodes = [default(node,fields) for node in nodes]
#    nodes = [node2bin(node,fields,fmt) for node in nodes]
#
#    # write output file
#    open(filename,'w').write(''.join(nodes))

# ==============================================================================
# test routines
# ==============================================================================

if __name__=='__main__':

  # set documentation
  doc = '''
GPBS test function. To test:

1.  Create text-files with the relevant output::

      qstat -f > qstat.txt
      pbsnodes > pbs.txt
      ganglia disk_total disk_free bytes_in bytes_out cpu_idle > ganglia.txt

2.  Test the gpbs-module::

      python gpbs.py qstat.txt pbs.txt ganglia.txt
'''
  # set argument parser
  import argparse
  form   = lambda prog: argparse.RawDescriptionHelpFormatter(prog,max_help_position=27)
  parser = argparse.ArgumentParser(\
    formatter_class=form,\
    description=doc,\
  )
  # add arguments
  parser.add_argument('files', metavar='FILE', type=str, nargs=3,
    help='Command output: qstat.txt pbs.txt ganglia.txt')
  # read arguments
  args = parser.parse_args()
  # convert
  (qstat,pbs,ganglia) = args.files

  # read job-information
  jobs = qstatRead(open(qstat,'r').read())
  # read pbs/ganglia output
  pbs = pbsRead(open(pbs,'r').read(),open(ganglia,'r').read())

  print ' '.join([str(job.id) for job in jobs])
  print ' '.join([node.name for node in pbs])
