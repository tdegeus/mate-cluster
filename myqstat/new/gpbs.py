'''
Description
-----------

This module provides functions to read the `qstat`, `pbsnodes` and `ganglia`
command (functions: "stat", "qstatRead", "pbsRead"). The data is stored as lists
of the "Job" and the "Node" classes.

Both the "Job" and the "Node" class have fields to the "String"-class. Therefore
these classes have the special feature that::

  example.test    == ``<str>``
  example['test'] == ``<?>``   # class depends on the raw data

Specifically each field have the following parameters::

  example.test.data   # raw data
  example.test.fmt    # print format
  example.test.color  # print colors as string (see gpbs.Color)
  example.test.trunc  # symbol to truncate the output string

Classes and functions
---------------------

**Color**

  The color style: interpretation of colors e.g. 'selection'.

**String**

  Provide storage of raw-data together with print format and color.

**Job**

  Job information.

**Node**

  Node information.

**qstatRead**

  Convert `qstat -f` command to list of jobs.

**pbsRead**

  Convert `pbsnodes` and `ganglia` command to list of nodes.

**stat**

  Convert `qstat -f`, `pbsnodes`, and `ganglia` commands to lists of jobs and
  nodes, with color coding depending on the output.

Copyright
---------

T.W.J. de Geus (tom@geus.me)
'''

# ==============================================================================
# class with colors
# ==============================================================================

class Color(object):
  '''
Database to define colors for different "operations". This class acts as the
style file for color highlighting.
  '''

  selection   = '\033[32m'  # green
  softwarning = '\033[35m'  # red
  warning     = '\033[31m'  # red
  free        = '\033[32m'  # green
  end         = '\033[0m'   # no set color

# ==============================================================================
# custom string class, for custom format print
# ==============================================================================

class String(object):
  '''
Description
-----------

Class to store data but also the print format (including color). This class is
used to store all data at the same place with the print settings.
  '''

  # ----------------------------------------------------------------------------
  # class constructor
  # ----------------------------------------------------------------------------

  def __init__(self,**kwargs):
    '''
Input options
-------------

**data**

  The raw-data. Can be of any class.

**fmt** = ``<str>``

  The print format, e.g. "%-10s". If a length is specified this is strictly
  enforced. I.e. if a string is too long it will be truncated.

**color** = [``None``] | ``<str>``

  Select color to print the string in. If set to ``None`` no color is applied to
  the output. See "gpbs.Color" for implemented colors.

**trunc** = ["..."] | ``<str>``

  Symbol to indicate that a string has been truncated. N.B. the length of the
  string is strictly enforced. I.e. the length that is specified includes the
  truncation symbol.
    '''

    self.data    = kwargs.pop( 'data'   , None  )
    self.color   = kwargs.pop( 'color'  , None  )
    self.trunc   = kwargs.pop( 'trunc'  , '...' )
    self.fmt     = kwargs.pop( 'fmt'    , None  )

  # ----------------------------------------------------------------------------
  # convert print format to string
  # ----------------------------------------------------------------------------

  def fmt2len(self):
    '''
Description
-----------

Convert the print format the length. For example::

  '%-20s'   --> 20
  '%16.8e'  --> 16
  '%s'      --> None

Returns
-------

**N** = ``<int>`` | ``None``

  The length of the string. Return ``None`` if the length of the string is not
  explicitly specified.
    '''

    import re

    try:
      return int(re.split('[a-z]',re.split('%[+-]?',self.fmt)[1].split('.')[0])[0])
    except:
      return None

  # ----------------------------------------------------------------------------
  # apply length to print format
  # ----------------------------------------------------------------------------

  def len2fmt(self,N):
    '''
Description
-----------

Apply length to print format.

Input arguments
---------------

**N** = ``<int>``

  The desired length of the string. To remove a pre-specified length use an
  empty string ("") as input.
    '''

    # get the current length: to replace
    length = self.fmt2len()

    # apply the length
    if length is None:
      self.fmt = self.fmt[:-1]+str(N)+self.fmt[-1]
    elif len(self.fmt.split('.'))>1:
      self.fmt = self.fmt.replace(str(length)+'.',str(N)+'.')
    else:
      self.fmt = self.fmt.replace(str(length),str(N))

  # ----------------------------------------------------------------------------
  # calculate the length of the string
  # ----------------------------------------------------------------------------

  def __len__(self):

    # read the length specified by the print format
    length = self.fmt2len()

    # return the length of the string:
    # - set by the format (self.fmt)
    # - empty string
    # - length of the string
    if length is not None:
      return length
    elif self.data is None:
      return 0
    else:
      return len(self.fmt%self.data)

  # ----------------------------------------------------------------------------
  # convert to formatted string
  # ----------------------------------------------------------------------------

  def __str__(self):

    import re

    # check
    if self.fmt is None:
      raise IOError('Unspecified "fmt"')

    # extract length from the print format
    length = self.__len__()

    # return empty string (of correct length) if there is not data
    if self.data is None:
      if length is not None:
        return ' '*length
      else:
        return ''

    # convert to string
    string = self.fmt % self.data

    # if needed: truncate string
    if length is not None:
      if len(string)>length:
        string = string[:length-len(self.trunc)] + self.trunc

    # return with the set color
    if self.color is None:
      return string
    else:
      return getattr(Color,self.color) + string + Color.end

# ==============================================================================
# job host(s)
# ==============================================================================

class Host(object):
  '''
Description
-----------

Class to store host information, and print is in an easily readable format.
The following information is stored:

* node: list with node numbers
* cpu:  list with CPU-numbers of the corresponding node
  '''

  # ----------------------------------------------------------------------------
  # class constructor
  # ----------------------------------------------------------------------------

  def __init__(self,*args,**kwargs):
    '''
Input arguments
---------------

**text** = ``<str>``, *optional*

  String in the following format: "compute-0-1/12+compute-0-1/1".

Input options
-------------

**node** = ``<list>``

  List with node numbers.

**cpu** = ``<list>``

  List with CPU numbers.
    '''

    # check the number of arguments
    if len(args)>1:
      raise IOError('Unknown number of input arguments')

    # read from text
    if len(args)==1:
      # remove the "compute-0-" and split at "+"
      text = args[0].replace("compute-0-","").split("+")
      # store nodes and cpu
      if any([len(i.split('/'))>1 for i in text]):
        self.node = [int(i.split("/")[0]) for i in text]
        self.cpu  = [int(i.split("/")[1]) for i in text]
      else:
        self.node = [int(i) for i in text]
        self.cpu  = []

    # optional overwrite with options
    self.node = kwargs.pop( 'node' , getattr(self,'node',None) )
    self.cpu  = kwargs.pop( 'cpu'  , getattr(self,'cpu' ,None) )

  # ----------------------------------------------------------------------------
  # combine hosts
  # ----------------------------------------------------------------------------

  def __add_(self,other):
    return Host(node=self.node+other.node,cpu=self.cpu+other.cpu)

  # ----------------------------------------------------------------------------
  # comparison of two instances of the host class
  # ----------------------------------------------------------------------------

  def __cmp__(self,other):
    '''
Description
-----------

Compare two instances of the host class.

Input arguments
---------------

**other** = ``<Host>``, ``<str>``

  An instance of the host class. If it is a string, the input is first converted
  to the ``<Host>``-class.
    '''

    # catch None arguments
    if type(other)==type(None):
      return -1

    # allow for several comparison types
    if type(other)==str:
      other = Host(other)
    elif type(other)==int:
      other = Host(node=[other])
    elif type(other)==list:
      other = Host(node= other )

    # check if any of the nodes match
    if len([True for i in self.node if i in other.node])>0:
      return 0

    # compare not matching host
    if min(self.node) < min(other.node):
      return -1
    elif min(self.node) > min(other.node):
      return +1
    else:
      return  0

  # ----------------------------------------------------------------------------
  # number of CPUs
  # ----------------------------------------------------------------------------

  def __len__(self):
    return len(self.node)

  # ----------------------------------------------------------------------------
  # write humanly readable output, and create alias for print command
  # ----------------------------------------------------------------------------

  def __repr__(self):
    return self.write()
  def __str__(self):
    return self.write()

  def write(self):
    '''
Description
-----------

Create human readable output. E.g.::

  node = [1,1,1,1]  --> "1"
  node = [1,1,1,2]  --> "1*"
    '''

    # no host: return empty string
    if self.node is None:
      return ''

    # return the host / one of the hosts
    node = self.node
    if node.count(node[0])==len(node):
      return "%d" % node[0]
    else:
      return "%d%s" % (node[0],"*")

# ==============================================================================
# job resources: nodes/CPUs
# ==============================================================================

class ResNode(object):
  '''
Description
-----------

Class to store the CPU-capacity reserved for a job. It can contain: the amount
of nodes, the amount of CPUs, and the type of CPU.
  '''

  # ----------------------------------------------------------------------------
  # class constructor
  # ----------------------------------------------------------------------------

  def __init__(self,*args,**kwargs):
    '''
Input arguments
---------------

**text** = ``<str>``, *optional*

  String of the format "1:ppn=2:intel" (2 CPUs on 1 node of type "intel").

Input options
-------------

**nnode** = ``<int>``

  Number of nodes.

**ncpu** = ``<int>``

  Number of CPUs.

**ctype** = ``<str>``

  Type of processor.
    '''

    # check number of arguments
    if len(args)>1:
      raise IOError('Unknown number of input arguments')

    # read from input text
    if len(args)==1:
      # append text with ":" for splitting
      text = args[0]+':'
      # loop until there are no more arguments left
      while len(text.split(':'))>1:
        # extract the argument
        (arg,text) = text.split(':',1)
        # extract the data
        if len(arg.split('ppn='))>1:
          self.ncpu = int(arg.replace('ppn=',''))
        else:
          arg = arg.replace('nodes=','')
          try:
            self.nnode = int(arg)
          except:
            self.ctype = arg

    # optional overwrite with options
    self.nnode = kwargs.pop( 'nnode' , getattr(self,'nnode',None) )
    self.ncpu  = kwargs.pop( 'ncpu'  , getattr(self,'ncpu' ,None) )
    self.ctype = kwargs.pop( 'ctype' , getattr(self,'ctype',None) )

  # ----------------------------------------------------------------------------
  # compare two variables of the ResNode class
  # ----------------------------------------------------------------------------

  def __cmp__(self,other):
    '''
Description
-----------

Compare two arguments of the "ResNode" class.
    '''
    default = lambda x: 1 if x is None else x

    if default(self.nnode)*default(self.ncpu) < default(other.nnode)*default(other.ncpu):
      return -1
    elif default(self.nnode)*default(self.ncpu) > default(other.nnode)*default(other.ncpu):
      return +1
    else:
      return  0

  # ----------------------------------------------------------------------------
  # write humanly readable output, and create alias for print command
  # ----------------------------------------------------------------------------

  def __repr__(self):
    return self.write()
  def __str__(self):
    return self.write()

  def write(self):
    '''
Description
-----------

Convert to human readable string, of the format "1:2:i". For this example the
owner has requested 1 node, 2 CPUs, of the intel class.
    '''
    text = ''
    if self.nnode is not None:
      text += str(self.nnode)
    text += ':'
    if self.ncpu is not None:
      text += str(self.ncpu)
    text += ':'
    if self.ctype is not None:
      text += self.ctype[0]
    return text

  # ----------------------------------------------------------------------------
  # return to pbs options
  # ----------------------------------------------------------------------------

  def pbsopt(self):
    '''
Description
-----------

Write as PBS-string
    '''

    default = lambda x: 1 if x is None else x

    text = [
      'nodes=%d' % default(self.nnode) ,
      'ppn=%d'   % default(self.ncpu ) ,
    ]

    if self.ctype is not None:
      text.append(self.ctype)

    return ':'.join(text)

# ==============================================================================
# class to store an object with a unit (e.g. Time = 1d)
# ==============================================================================

class Unit(object):
  '''
Description
-----------

A generic class to view and read floats that have a unit. For example a float
with the unit of time: "1d".
  '''

  # ----------------------------------------------------------------------------
  # class constructor
  # ----------------------------------------------------------------------------

  def __init__(self,*args,**kwargs):

    if len(args)==1:
      if type(args[0])==str:
        self.data = self.str2float(args[0])
      else:
        self.data = args[0]

    self.data = kwargs.pop( 'data' , getattr(self,'data',None) )

  # ----------------------------------------------------------------------------
  # functions to convert to float or string, makes comparison easy
  # ----------------------------------------------------------------------------

  def __float__(self):
    if self.data is None:
      return 0.0
    else:
      return self.data

  def __int__(self):
    return int(float(self))

  # ----------------------------------------------------------------------------
  # alias to print
  # ----------------------------------------------------------------------------

  def __repr__(self):
    return self.__str__()

  def __str__(self):
    return self.write()

  # ----------------------------------------------------------------------------
  # subtract: output of the same class
  # ----------------------------------------------------------------------------

  def __sub__(self,other):

    if self.__class__ != other.__class__:
      raise IOError('Arguments must have the same class')

    return globals()[self.__class__.__name__](self.data-other.data)

  # ----------------------------------------------------------------------------
  # add: output of the same class
  # ----------------------------------------------------------------------------

  def __add__(self,other):

    if self.__class__ != other.__class__:
      raise IOError('Arguments must have the same class')

    return globals()[self.__class__.__name__](self.data+other.data)

  # ----------------------------------------------------------------------------
  # right add: to use sum
  # ----------------------------------------------------------------------------

  def __radd__(self,other):
    return globals()[self.__class__.__name__](self.data+other)

  # ----------------------------------------------------------------------------
  # divide: output has no unit
  # ----------------------------------------------------------------------------

  def __div__(self,other):

    if self.data is not None and other is not None:
      return float(self)/float(other)
    else:
      return None

  # ----------------------------------------------------------------------------
  # comparison to other object (==, <, >, etc.)
  # ----------------------------------------------------------------------------

  def __cmp__(self,other):
    '''
Description
-----------

Compare to other object (==, <, >, etc.). The other object can be of many types
and is converted to a float to do the comparison.

If the other object is a string
    '''

    # convert string to float
    # - if the comparison is embedded in the string (e.g. ">10d") the comparison
    #   is directly done
    # - otherwise the comparison below is used
    if type(other)==str:

      import re

      # split operator from value, and convert value to own class
      compare = re.split('[0-9]',other)[0]
      other   = self.str2float(other.replace(compare,''))

      # perform comparison, the '-1' is arbitrarily unequal to 0
      if len(compare)>0:
        if eval('float(self) %s other' % compare):
          return 0
        else:
          return -1

    # compare to other values: class/float/int
    if float(self) < float(other):
      return -1
    elif float(self) > float(other):
      return +1
    else:
      return  0


# ==============================================================================
# Time class: derived of the Unit class, and thus similar to Data
# ==============================================================================

class Time(Unit):
  '''
Description
-----------

Class to store time, and print is in an easily readable format.
  '''

  # ----------------------------------------------------------------------------
  # convert string (or float) to float
  # ----------------------------------------------------------------------------

  def str2float(self,arg):
    '''
Input arguments
---------------

**text** = ``<float>`` | ``<str>``

  Time in:
  * ``<float>``: number of seconds
  * ``<str>``  : time in clock format, "HH:MM:SS"
  * ``<str>``  : time in a single unit, e.g. "1m"
    '''

    # if the input is None: return as None immediately
    if arg is None:
      return None

    # if the input is a float: return immediately
    if type(arg)==float or type(arg)==int:
      return float(arg)

    # clock format: convert and return
    if len(arg.split(':'))>=2:
      arg = arg.split(":")
      return float(int(arg[0])*60*60+int(arg[1])*60+int(arg[2]))

    # set conversion ratio
    ratio = {
      'd' : 60.0*60.0*24.0 ,
      'h' : 60.0*60.0      ,
      'm' : 60.0           ,
      's' : 1.0            ,
    }

    # check if the string has one of the units, if so convert and return
    unit = arg[-1]
    if unit in ratio:
      return float(arg.split(unit)[0])*ratio[unit]

    # final possibility: string without a unit
    try:
      return float(arg)
    except:
      raise IOError('Unknown input string "%s"' % arg)

  # ----------------------------------------------------------------------------
  # write output
  # ----------------------------------------------------------------------------

  def write(self,precision=None):
    '''
  Description
  -----------

  Create human readable output. E.g.::

    24*60*60 == "1.0d"
    '''

    # set the sign
    if self.data < 0.0:
      sign = '-'
    else:
      sign = ''

    # set conversion factors (days,hours,minutes,seconds)
    ratio = {}
    ratio[60.0*60.0*24.0] = 'd'
    ratio[60.0*60.0     ] = 'h'
    ratio[60.0          ] = 'm'
    ratio[1.0           ] = 's'

    for fac in sorted(ratio)[-1::-1]:
      if abs(float(self))>=fac:
        # set precision default, based on scaled output
        if precision is None:
          if abs(float(self))/fac>=10:
            precision = 0
          else:
            precision = 1
        # return output
        return sign+('%1.'+str(precision)+'f'+ratio[fac])%(abs(float(self))/fac)

    return ''


# ==============================================================================
# Data class: derived of the Unit class, and thus similar to Time
# ==============================================================================

class Data(Unit):
  '''
Description
-----------

Class to store data, and print is in an easily readable format.
  '''

  # ----------------------------------------------------------------------------
  # class constructor
  # ----------------------------------------------------------------------------

  def str2float(self,arg):
    '''
Input arguments
---------------

**text** = ``<float>`` | ``<str>``

  Data in:
  * ``<float>``: number of bytes
  * ``<str>``  : humanly readable string, e.g. "1gb"
    '''

    # if the input is None: return as None immediately
    if arg is None:
      return None

    # if the input is a float: return immediately
    if type(arg)==float or type(arg)==int:
      return float(arg)

    # set conversion ratio
    ratio = {
      'tb' : 1.0e12 ,
      'gb' : 1.0e9  ,
      'mb' : 1.0e6  ,
      'kb' : 1.0e3  ,
      'b'  : 1.0    ,
      'T'  : 1.0e12 ,
      'G'  : 1.0e9  ,
      'M'  : 1.0e6  ,
      'K'  : 1.0e3  ,
    }

    # check if the string has one of the units, if so convert and return
    for i in [2,1]:
      if len(arg)>i:
        unit = arg[-i:]
        if unit in ratio:
          return float(arg.split(unit)[0])*ratio[unit]

    # final possibility: string without a unit
    try:
      return float(arg)
    except:
      raise IOError('Unknown input string "%s"' % arg)

  # ----------------------------------------------------------------------------
  # write humanly readable output, and create alias for print command
  # ----------------------------------------------------------------------------

  def write(self,precision=0):
    '''
Description
-----------

Create human readable output. E.g.::

  1000.0 == "1mb"
    '''
    # set conversion factors
    ratio = {}
    ratio[1.0e12] = 'tb'
    ratio[1.0e9 ] = 'gb'
    ratio[1.0e6 ] = 'mb'
    ratio[1.0e3 ] = 'kb'
    ratio[1.0e0 ] = 'b'
    for fac in sorted(ratio)[-1::-1]:
      if float(self)>=fac:
        return ('%1.'+str(precision)+'f'+ratio[fac])%(float(self)/fac)

    return ''

# ==============================================================================
# generic class to store a job/node
# ==============================================================================

class Item(object):

  # ----------------------------------------------------------------------------
  # write to screen
  # ----------------------------------------------------------------------------

  def __str__(self):
    return self.write()

  def __repr__(self):
    return self.write()

  # ----------------------------------------------------------------------------
  # function to use e.g. self['id'] to access the raw data
  # ----------------------------------------------------------------------------

  def __getitem__(self,key):
    return getattr(self,key).data

  # ----------------------------------------------------------------------------
  # check if the arguments are specified and not None
  # ----------------------------------------------------------------------------

  def check(self,*args):
    '''
Description
-----------

Check if all arguments are specified and not ``None``. Only in this case does
this function return ``True``, otherwise ``False`` is returned.

Input arguments
---------------

**args** = ``<str>``

  The names of the fields to check.
    '''

    for arg in args:
      if not hasattr(self,arg):
        return False
      if getattr(self,arg) is None:
        return False

    return True


# ==============================================================================
# class to store an individual job
# ==============================================================================

class Job(Item):
  '''
Description
-----------

Class to store the job information. Each field of this class is stored using the
custom "gpbs.String" class. To read:

- a string: ``job.example``
- the raw data: ``job['example']``

To modify the data, or the print format use::

  job.example.data
  job.example.fmt
  job.example.color
  job.example.trunc
  '''

  # ----------------------------------------------------------------------------
  # class constructor
  # ----------------------------------------------------------------------------

  def __init__(self,*args,**kwargs):
    '''
Input arguments
---------------

**text** = ``<str>``

  The output of the `qstat -f` command for this job. I.e.::

    text << `qstat -f`
    Job(text.split(Job Id:))

Input options
-------------

========= ========= ============================================================
field     type      description
========= ========= ============================================================
id        <str>     id (as string)
name      <str>     name
owner     <str>     owner
state     <str>     status of the job (R=running, Q=queued, E=exiting)
resnode   <ResNode> claimed nodes/CPUs
cputime   <Time>    time that the job has been consuming CPU resources
walltime  <Time>    time that the job has been running
host      <Host>    job that is running the job
score     <float>   score: ratio between the 'cputime' and the 'walltime'
========= ========= ============================================================
    '''

    # check number of input arguments
    if len(args)>1:
      raise IOError('Unknown number of input arguments')

    # (a) read input text
    if len(args)==1:
      # name alias
      text = args[0]
      # split/convert the different parts
      self.id       = text.split('\n')[0].split('.')[0].strip()
      self.name     = csplit(text,'Job_Name'                               )
      self.owner    = csplit(text,'Job_Owner'                              ).split('@')[0]
      self.state    = csplit(text,'job_state'                              )
      self.resnode  = csplit(text,'Resource_List.nodes'    ,dtype='ResNode')
      self.pmem     = csplit(text,'Resource_List.pmem'     ,dtype='Data'   )
      self.memused  = csplit(text,'resources_used.mem'     ,dtype='Data'   )
      self.cputime  = csplit(text,'resources_used.cput'    ,dtype='Time'   )
      self.walltime = csplit(text,'resources_used.walltime',dtype='Time'   )
      self.host     = csplit(text,'exec_host'              ,dtype='Host'   )

    # (b) store from input (overwrites read data)
    for key in kwargs:
      setattr(self,key,kwargs[key])

    # calculate the job's score
    if not hasattr(self,'score'):
      if self.check('cputime','host','walltime'):
        self.score = float(self.cputime)/(float(self.walltime)*float(len(self.host)))
      else:
        self.score = None

    # convert each field to a field of the string class:
    # - to print            : self.id
    # - to use the raw data : self['id']
    self.id       = String(data=self.id      ,fmt='%s'   )
    self.name     = String(data=self.name    ,fmt='%-s'  )
    self.owner    = String(data=self.owner   ,fmt='%-s'  )
    self.state    = String(data=self.state   ,fmt='%-s'  )
    self.resnode  = String(data=self.resnode ,fmt='%s'   )
    self.pmem     = String(data=self.pmem    ,fmt='%s'   )
    self.memused  = String(data=self.memused ,fmt='%s'   )
    self.cputime  = String(data=self.cputime ,fmt='%s'   )
    self.walltime = String(data=self.walltime,fmt='%s'   )
    self.host     = String(data=self.host    ,fmt='%s'   )
    self.score    = String(data=self.score   ,fmt='%4.2f')

  # ----------------------------------------------------------------------------
  # write (formatted) string, create alias for print command
  # ----------------------------------------------------------------------------

  def write(self):
    return str(self.id)

# ==============================================================================
# compute node information
# ==============================================================================

class Node(Item):
  '''
Description
-----------

Class to store the node-information. Each field of this class is stored using the
custom "gpbs.String" class. To read:

- a string: ``node.example``
- the raw data: ``node['example']``

To modify the data, or the print format use::

  node.example.data
  node.example.fmt
  node.example.color
  node.example.trunc
  '''

  # ----------------------------------------------------------------------------
  # class constructor
  # ----------------------------------------------------------------------------

  def __init__(self,*args,**kwargs):
    '''
Input arguments
---------------

**text** = ``<str>``

  The output of the `pbsnodes` command for this node. I.e.::

    text << `qpbsnodes`
    Node(text.split('\n\n'))

Input options
-------------

=========== =========== ========================================================
field       type        description
=========== =========== ========================================================
name        <str>       name of the compute-node
node        <int>       node number (compute-0-X -> int(X))
state       <str>       status (free,job-exclusive,down,offline)
ncpu        <int>       number of CPUs
ctype       <str>       type of node (intel,amd)
jobs        <list>      list of job numbers <int>
memt        <Data>      total memory
mema        <Data>      available memory
memu        <Data>      memory in use
memp        <Data>      physical memory
disk_total  <Data>      total disk space
disk_free   <Data>      free disk space
bytes_in    <Data>      network traffic in-bound
bytes_out   <Data>      network traffic out-bound
cpu_idle    <float>     CPU idle (waiting) percentage
=========== =========== ========================================================
    '''

    # support function, split jobs: 0/X.hostname
    def jsplit(txt):
      try:
        jobs = txt.split('jobs =')[1].split('\n')[0].strip().split(',')
        return [int(i.split('/')[1].split('.')[0].strip()) for i in jobs]
      except:
        return []

    # check number of input arguments
    if len(args)>1:
      raise IOError('Unknown number of input arguments')

    # set function to convert GB to B
    giga = lambda x: None if x is None else float(x)*1.0e9

    # (a) read ganglia output
    self.disk_total = Data( giga( kwargs.pop( 'disk_total' , None ) ) )
    self.disk_free  = Data( giga( kwargs.pop( 'disk_free'  , None ) ) )
    self.bytes_in   = Data(       kwargs.pop( 'bytes_in'   , None )   )
    self.bytes_out  = Data(       kwargs.pop( 'bytes_out'  , None )   )
    self.cpu_idle   =             kwargs.pop( 'cpu_idle'   , None )

    # (b) read input string to pbsnodes command
    if len(args)==1:
      # alias the input text
      text = args[0]
      # read different fields
      self.name  = text.split('\n')[0]
      self.state = csplit(text,'state'                                    )
      self.ncpu  = csplit(text,'np'                          ,dtype='int' )
      self.ctype = csplit(text,'properties'                               )
      self.jobs  = jsplit(text                                            )
      self.memt  = csplit(text,'totmem'  ,postfix='=',sep=',',dtype='Data')
      self.memp  = csplit(text,'physmem' ,postfix='=',sep=',',dtype='Data')
      self.mema  = csplit(text,'availmem',postfix='=',sep=',',dtype='Data')

    # (c) copy from input (overwrites input from the pbsnodes command)
    for key in kwargs:
      setattr(self,key,kwargs.pop(key))

    # calculate available memory
    if not hasattr(self,'memu'):
      if self.check('memt','mema'):
        self.memu = Data(self.memt-self.mema)
      else:
        self.memu = None

    # calculate node number
    try:
      self.node = int(self.name.replace('compute-0-',''))
    except:
      self.node = None

    # calculate the number of free CPUs
    if not hasattr(self,'cpufree'):
      self.cpufree = 0
      if self.state not in ['offline','down']:
        if self.check('jobs'):
          self.cpufree = self.ncpu-len(self.jobs)
        else:
          self.cpufree = self.ncpu

    # convert each field to a field of the string class:
    # - to print            : self.name
    # - to use the raw data : self['name']
    self.node       = String(data=self.node         ,fmt='%d')
    self.name       = String(data=self.name         ,fmt='%s')
    self.state      = String(data=self.state        ,fmt='%s')
    self.ncpu       = String(data=self.ncpu         ,fmt='%d')
    self.cpufree    = String(data=self.cpufree      ,fmt='%d')
    self.ctype      = String(data=self.ctype        ,fmt='%s')
    self.jobs       = String(data=self.jobs         ,fmt='%s')
    self.memt       = String(data=self.memt         ,fmt='%s')
    self.memp       = String(data=self.memp         ,fmt='%s')
    self.mema       = String(data=self.mema         ,fmt='%s')
    self.memu       = String(data=self.memu         ,fmt='%s')
    self.disk_total = String(data=self.disk_total   ,fmt='%s')
    self.disk_free  = String(data=self.disk_free    ,fmt='%s')
    self.bytes_in   = String(data=self.bytes_in     ,fmt='%s')
    self.bytes_out  = String(data=self.bytes_out    ,fmt='%s')
    self.cpu_idle   = String(data=self.cpu_idle     ,fmt='%f')

  # ----------------------------------------------------------------------------
  # write (formatted) string, create alias for print command
  # ----------------------------------------------------------------------------

  def write(self):
    return self.name

# ==============================================================================
# support function to split text
# ==============================================================================

def csplit(text,name,postfix=' =',sep='\n',dtype=None):
  '''
Split a string, and convert to a specific data type.

Input arguments
---------------

**text** = ``<str>``

  String to split/convert.

**name** = ``<str>``

  Key-name, at which to split the string (in front of the data).

Input options
-------------

**postfix** = ``<str>``

  Post-fix of the key-name (in front of the data).

**sep** = ``<str>``

  Separator (after the data).

**dtype** = [None] | int | float | Data | Time | ResNode | Host | ...

  Data-type to which to convert the data.

Output arguments
----------------

**data** = [``<str>``] | ...

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

  csplit(text,'resources_used.mem',dtype='Data')
  '''

  import re

  # split the text
  try:
    text = re.sub(' +',' ',text).strip().split(name+postfix)[1].split(sep)[0].strip()
  except:
    return None

  # convert the data-type
  if dtype is not None:
    return eval('%s(text)'%dtype)
  else:
    return text

# ==============================================================================
# convert `qstat -f` output
# ==============================================================================

def qstatRead(qstat=None):
  '''
Description
-----------

Read the output of the `qstat -f` command. The output is converted to a list of
jobs.

Input options
-------------

**qstat** = [``None``] | ``<str>``

  In stead of reading the `qstat -f` command, supply a string containing this
  output. Mostly used for debugging.

Output arguments
----------------

**jobs** = ``<list>``

  A list with jobs of the ``<Job>``-class.

See also
--------

* gpbs.Job
  '''

  # read output `qstat -f` command
  if qstat is None:
    import commands
    (stat,qstat) = commands.getstatusoutput('qstat -f')
    if stat:
      raise RuntimeError('Command "qstat -f" failed:\n %s'%qstat)

  # replace hard word-wrap, and split in jobs
  jobs = qstat.replace('\n\t','')
  jobs = jobs.split('Job Id:')[1:]
  # read/convert each job
  for (ijob,job) in enumerate(jobs):
    jobs[ijob] = Job(job)

  return jobs

# ==============================================================================
# convert `pbsnodes` and `ganglia` output
# ==============================================================================

def pbsRead(pbsnodes=None,ganglia=False):
  '''
Description
-----------

Read the output of the `pbsnodes` and the `ganglia` command. The output is
converted to a list of compute-nodes.

Input option
------------

**pbsnodes** = [``None``] | ``<str>``

  In stead of reading the `pbsnodes` command, supply a string containing this
  output. Mostly used for debugging.

**ganglia** = [``None``] | ``False`` | ``<str>``

  If set ``False`` the `ganglia` command is not read. This option is used to
  speed up, as the `ganglia` command is slow. If a ``<str>`` is supplied the
  `ganglia` command is also not read, but the output in the ``<str>`` is used
  in stead. Notice that the following command should be used to form the
  string::

    ganglia disk_total disk_free bytes_in bytes_out cpu_idle

Output arguments
----------------

**nodes** = ``<list>``

  A list with compute-nodes of the ``<Node>``-class.

See also
--------

* gpbs.Node
  '''

  # read the `pbsnodes` command
  if pbsnodes is None:
    import commands
    (stat,pbsnodes) = commands.getstatusoutput('pbsnodes')
    if stat:
      raise RuntimeError('Command "pbsnodes" failed:\n %s'%pbsnodes)
  # split the `pbsnodes` output in different nodes
  pbsnodes = filter(None,pbsnodes.split('\n\n'))

  # initiate the ganglia options, and the output
  args = ['disk_total','disk_free','bytes_in','bytes_out','cpu_idle']
  dat  = {}
  # read the `ganglia` command
  if ganglia is None or ganglia==True:
    import commands
    (stat,ganglia) = commands.getstatusoutput('ganglia '+' '.join(args))
    if stat:
      raise RuntimeError('Command "ganglia" failed:\n %s'%ganglia)
  # convert the `ganglia` command output to dictionary
  if ganglia is not False:
    # loop over lines: split lines and store in dictionary per node
    for line in ganglia.split('\n')[:-1]:
      out = filter(None,line.replace("\t","").split(" "))
      (name,out) = (out[0],out[1:])
      dat[name] = {arg:out[i] for (i,arg) in enumerate(args)}
  # change name
  ganglia = dat

  # loop over pbs-output (nodes) and convert to Node class
  for (ipbs,pbs) in enumerate(pbsnodes):
    # get node number
    node = pbs.split('\n')[0]
    # convert output, with or without ganglia options
    try:
      pbsnodes[ipbs] = Node(pbs,**ganglia[node])
    except:
      pbsnodes[ipbs] = Node(pbs)

  return pbsnodes

# ==============================================================================
# read all information at once
# ==============================================================================

def stat(qstat=None,pbsnodes=None,ganglia=False):
  '''
Description
-----------

Read the "qstat" and the "pbsnodes" commands, and apply colors to warn users of
potential misuse or problems.

Input options
-------------

**qstat** = [``None``] | ``<str>``

  The output of the `qstat -f` command. If set to ``None`` (default) the command
  is run inside this function.

**pbsnodes** = [``None``] | ``<str>``

  The output of the `pbsnodes` command. If set to ``None`` (default) the command
  is run inside this function.

**ganglia** = [``False``] | ``None`` | ``<str>``

  The output of the `ganglia` command. If set to ``None`` (default) the command
  is run inside this function. If set to ``False`` no ganglia information is
  read. If the input is a string the extact arguments must have been used to run
  the command.

See also
--------

* gpbs.qstatRead / gpbs.Job
* gpbs.pbsRead   / gpbs.Node
  '''

  # read all running jobs, and all node information
  jobs  = qstatRead(qstat=qstat)
  nodes = pbsRead(pbsnodes=pbsnodes,ganglia=ganglia)
  # convert nodes to dictionary for easly lookup
  ndict = {}
  for node in nodes:
    ndict[node['node']] = node

  # check the job's score:
  # < 0.8 : soft warning
  # > 1.03: warning
  for job in jobs:
    if job['score'] < 0.8:
      job.score.color = 'softwarning'
    elif job['score'] > 1.03:
      job.score.color = 'warning'

  # check the job's memory usage
  # - less than 10% free memory remaining of host: warning
  # - more that 1gb of memory without claim: soft warning
  for job in jobs:
    for n in set(job['host'].node):
      if ndict[n]['mema']/ndict[n]['memt'] < 0.1:
        job.memused.color = 'warning'
      elif job['memused']>Data('1gb') and job['pmem'] is None and job['resnode'].ncpu < ndict[n]['ncpu']:
        job.memused.color = 'softwarning'

  # check the node's memory
  for node in nodes:
    if node['mema'] is not None and node['memt'] is not None:
      if node['mema']/node['memt'] < 0.1:
        node.mema.color = 'warning'

  # check the node's disk space
  for node in nodes:
    if node['disk_free'] is not None and node['disk_total'] is not None:
      if node['disk_free']/node['disk_total'] < 0.1:
        node.disk_free.color = 'warning'

  # check the number of free CPUs per node
  for node in nodes:
    if node['cpufree']>0:
      node.cpufree.color = 'free'

  # return the jobs and node
  return (jobs,nodes)

# ==============================================================================
# designated for testing
# ==============================================================================

if __name__=='__main__':
  pass
