'''
This module provides functions to read the ``qstat``, ``pbsnodes`` and
``ganglia`` commands.

:print:

  To read and print information, use:

  * ``gpbs.Print.myqstat``
  * ``gpbs.Print.myqstat_user``
  * ``gpbs.Print.myqstat_node``

:list:

  To obtain a list with information per job/user/node, use:

  * ``gpbs.myqstat``     : a list of ``<gpbs.Job>``
  * ``gpbs.myqstat_user``: a list of ``<gpbs.Owner>``
  * ``gpbs.myqstat_node``: a list of ``<gpbs.Node>``

  All these classes have the customized functionality to obtain a field as data or
  as string (with a certain formatting default). Consider the following example::

    >>> type(job.cputime)
    <class 'gpbs.Time'>

    >>> type(job['cputime'])
    <str>

  Custom print formatting is also available. Consider the following example to
  print a list of jobs in columns (namely: "id", "host" and "pmem")::

    for job in jobs:
      print '{job.id:>6.6s}, {job.host:>3s}, {job.pmem:>5s}'.format(job=job)

  This can be automated using::

    # without any color definition

    jobs[0].print_header(...)

    for job in jobs:
      print job.print_column(...)

    # with color definition

    jobs[0].print_header(...).format(color=gpbs.ColorDefault)

    for job in jobs:
      print job.print_column(...).format(color=gpbs.ColorDefault)

:copyright:

  | T.W.J. de Geus
  | http://www.geus.me
  | tom@geus.me
'''

import re,os

################################################################################
# --------------------------- PART 1 - DATA CLASSES ---------------------------
################################################################################

# ==============================================================================
# job host(s)
# ==============================================================================

class Host(object):
  r'''
Class to store host information. This class can be used to print the host
information in a compact way. Thereby, only the node-number is included as
follows::

  node = [1,1,1,1]  --> "1"
  node = [1,1,1,2]  --> "1*"

:arguments:

  **text** (``<str>``), *optional*
    String in the following format: "compute-0-1/12+compute-0-1/1".

:options/fields:

  **node** (``<list>``)
    List with node numbers.

  **cpu** (``<list>``)
    List with CPU numbers.

:print format:

  The print format may be of the following type::

    {:[align][width].[precision]}

  The 'precision' can be ``0,1,2``, as shown in the following example::

    >>> gpbs.Host('compute-0-1/2+compute-0-2/3')
    1*

    >>> '{:.1}'.format(gpbs.Host('compute-0-1/2+compute-0-2/3'))
    1,2

    >>> '{:.2}'.format(gpbs.Host('compute-0-1/2+compute-0-2/3'))
    1/2,2/3
  '''

  # ----------------------------------------------------------------------------
  # class constructor
  # ----------------------------------------------------------------------------

  def __init__(self,*args,**kwargs):

    # check the number of arguments
    if len(args)>1:
      raise IOError('Unknown number of input arguments')

    # read from text
    if len(args)==1:
      if args[0] is not None and args[0] is not '':
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
    self.node = kwargs.pop( 'node' , getattr(self,'node',[]) )
    self.cpu  = kwargs.pop( 'cpu'  , getattr(self,'cpu' ,[]) )

  # ----------------------------------------------------------------------------
  # combine hosts
  # ----------------------------------------------------------------------------

  def __add__(self,other):
    return Host(node=self.node+other.node,cpu=self.cpu+other.cpu)

  def __radd__(self,other):
    if type(other)==int:
      return other + len(self.node)
    else:
      other.node += self.node
      other.cpu  += self.cpu

  # ----------------------------------------------------------------------------
  # comparison of two instances of the host class
  # ----------------------------------------------------------------------------

  def __cmp__(self,other):
    '''
Compare two instances of the ``<Host>``-class.

:arguments:

  **other** (``<Host>`` | ``<str>``)
    Quantity to compare with. If it is a string, the input is first converted to
    the ``<Host>``-class.
    '''

    # catch None arguments
    if type(other)    == type(None): return -1
    if len(self.node) == 0         : return -1

    # allow for several comparison types
    if   type(other)==str : other = Host(      other )
    elif type(other)==int : other = Host(node=[other])
    elif type(other)==list: other = Host(node= other )

    # check if any of the nodes match
    if len([True for i in self.node if i in other.node])>0:
      return 0

    # compare not matching host
    if   min(self.node) < min(other.node): return -1
    elif min(self.node) > min(other.node): return +1
    else                                 : return  0

  # ----------------------------------------------------------------------------
  # number of CPUs
  # ----------------------------------------------------------------------------

  def __len__(self):
    return len(self.node)

  # ----------------------------------------------------------------------------
  # convert to string
  # ----------------------------------------------------------------------------

  def __repr__(self):
    return self.__str__()

  def __str__(self):
    return '{}'.format(self)

  def __format__(self,fmt):

    # break up print format in pieces / set default
    if len(fmt)>0: fmt = re.split('([><^=+-]?)([0-9]*)(\.?)([0-9]*)(.*)',fmt)
    else         : fmt = ['','','','','','','']

    # set default precision
    precision = '0'
    # if print-format "f"loat: extract print precision
    if fmt[5] in ['f']:
      fmt[5] = 's'
      if len(fmt[4])>0:
        precision = fmt[4]
        fmt[4]    = ''
      else:
        precision = '0'

    # remove precision
    if len(fmt[4])==0:
      fmt[3] = ''

    # convert to print format
    fmt = '{:%s}'%''.join(fmt)

    # act on empty host
    if len(self.node)==0:
      return fmt.format(' ')

    # create text, based of print precision
    if precision=='0':
      if self.node.count(self.node[0])==len(self.node):
        return fmt.format(str(self.node[0]))
      else:
        return fmt.format(str(self.node[0])+'*')

    if precision=='1':
      return fmt.format(','.join([str(i) for i in self.node]))

    if precision=='2':
      return fmt.format(','.join([str(i)+'/'+str(j) for i,j in zip(self.node,self.cpu)]))

    raise IOError('Unknown print format')

# ==============================================================================
# job resources: nodes/CPUs
# ==============================================================================

class ResNode(object):
  r'''
Class to store the CPU-capacity reserved for a job. It can contain: the amount
of nodes, the amount of CPUs, and the type of CPU.

:arguments:

  **text** (``<str>``) *optional*
    String of the format "1:ppn=2:intel" (2 CPUs on 1 node of type "intel").

:options/fields:

  **nodes** (``<int>``)
    Number of nodes.

  **ppn** (``<int>``)
    Number of CPUs per node.

  **ctype** (``<str>``)
    Type of processor.

:print format:

  The print format may be of the following type::

    {:[align][width][type]}

  The *type* can be:

  * ``s`` or ``c`` (default): print in compact form
  * ``p``: print as PBS-option

  Consider the following example::

    >>> gpbs.ResNode('nodes=1:ppn=10:intel')
    1:10:i

    >>> '{:s}'.format(gpbs.ResNode('nodes=1:ppn=10:intel'))
    1:10:i

    >>> '{:p}'.format(gpbs.ResNode('nodes=1:ppn=10:intel'))
    nodes=1:ppn=10:intel
  '''

  # ----------------------------------------------------------------------------
  # class constructor
  # ----------------------------------------------------------------------------

  def __init__(self,*args,**kwargs):

    # check number of arguments
    if len(args)>1:
      raise IOError('Unknown number of input arguments')

    # read from input text
    if len(args)==1:
      if args[0] is not None and args[0] is not '':
        # extract node information from other resources
        text = args[0]
        if   len(text.split('nodes='))>1: text = 'nodes='+text.split('nodes=')[1].split(',')[0]
        elif len(text.split('ppn='  ))>1: text = 'ppn='  +text.split('ppn='  )[1].split(',')[0]
        else                            : text =          text.split(','     )[0]
        # read node information
        for arg in text.split(':'):
          if   len(arg.split('nodes='))>1: self.nodes = int(arg.split('nodes=')[1])
          elif len(arg.split('ppn='  ))>1: self.ppn   = int(arg.split('ppn='  )[1])
          else                           : self.ctype =     arg

    # optional overwrite with options
    self.nodes = kwargs.pop( 'nodes' , getattr(self,'nodes',1   ) )
    self.ppn   = kwargs.pop( 'ppn'   , getattr(self,'ppn'  ,1   ) )
    self.ctype = kwargs.pop( 'ctype' , getattr(self,'ctype',None) )

  # ----------------------------------------------------------------------------
  # count the number of CPUs
  # ----------------------------------------------------------------------------

  def __len__(self):
    return self.nodes*self.ppn

  # ----------------------------------------------------------------------------
  # compare two variables of the ResNode class
  # ----------------------------------------------------------------------------

  def __cmp__(self,other):
    '''
Compare two arguments of the "ResNode" class.
    '''
    default = lambda x: 1 if x is None else x

    if   default(self.nodes)*default(self.ppn) < default(other.nodes)*default(other.ppn): return -1
    elif default(self.nodes)*default(self.ppn) > default(other.nodes)*default(other.ppn): return +1
    else                                                                                : return  0

  # ----------------------------------------------------------------------------
  # convert to string
  # ----------------------------------------------------------------------------

  def __repr__(self):
    return self.__str__()

  def __str__(self):
    return '{}'.format(self)

  def __format__(self,fmt):

    # set default
    pbs = False

    # break apart print format
    if len(fmt)>0:
      if fmt[-1]=='p':
        pbs = True
        fmt = fmt[:-1]
      elif fmt[-1] in ['c','s']:
        fmt = fmt[:-1]

    # convert print format
    fmt = '{:%ss}'%fmt

    # print short-hand
    if not pbs:
      text = ''
      if self.nodes is not None: text +=     str(self.nodes)
      if self.ppn   is not None: text += ':'+str(self.ppn  )
      if self.ctype is not None: text += ':'+    self.ctype[0]
      return fmt.format(text)

    # print long
    text = [
      'nodes=%d' % self.nodes ,
      'ppn=%d'   % self.ppn   ,
    ]
    if self.ctype is not None:
      text.append(self.ctype)
    return fmt.format(':'.join(text))

# ==============================================================================
# class to store an object with a unit (e.g. Time = 1d)
# ==============================================================================

class Unit(object):
  r'''
A generic class to view and read floats that have a unit. For example a float
with the unit of time: "1d".

To complete the behavior of a child-class the following functions have to be
specified:

* ``<float> = str2float (self,arg)``: convert string to float (as return)
* ``<str>   = __format__(self,arg)``: formatted print

:argument/field:

  **arg** (``<int>`` | ``<float>`` | ``<str>``)
    The input data.
  '''

  # ----------------------------------------------------------------------------
  # class constructor
  # ----------------------------------------------------------------------------

  def __init__(self,arg):

    if   arg is None or arg is '': self.arg = None
    elif type(arg)==str          : self.arg = self.str2float(arg)
    else                         : self.arg = arg

  # ----------------------------------------------------------------------------
  # functions to convert to float or string, makes comparison easy
  # ----------------------------------------------------------------------------

  def __float__(self):
    if self.arg is None: return 0.0
    else               : return self.arg

  def __int__(self):
    return int(float(self))

  # ----------------------------------------------------------------------------
  # convert to string
  # ----------------------------------------------------------------------------

  def __repr__(self):
    return self.__str__()

  def __str__(self):
    return '{}'.format(self)

  # ----------------------------------------------------------------------------
  # subtract: output of the same class
  # ----------------------------------------------------------------------------

  def __sub__(self,other):

    if self.__class__ != other.__class__:
      raise IOError('Arguments must have the same class')

    return globals()[self.__class__.__name__](float(self)-float(other))

  # ----------------------------------------------------------------------------
  # add: output of the same class
  # ----------------------------------------------------------------------------

  def __add__(self,other):

    if self.__class__ != other.__class__:
      raise IOError('Arguments must have the same class')

    return globals()[self.__class__.__name__](float(self)+float(other))

  # ----------------------------------------------------------------------------
  # right add: to use sum
  # ----------------------------------------------------------------------------

  def __radd__(self,other):
    return globals()[self.__class__.__name__](float(other)+float(self))

  # ----------------------------------------------------------------------------
  # divide: output has no unit
  # ----------------------------------------------------------------------------

  def __div__(self,other):

    if self.arg is not None and other is not None:
      return float(self)/float(other)
    else:
      return None

  # ----------------------------------------------------------------------------
  # comparison to other object (==, <, >, etc.)
  # ----------------------------------------------------------------------------

  def __cmp__(self,other):
    '''
Compare to other object (==, <, >, etc.). The other object can be of many types
and is converted to a float to do the comparison.
    '''

    # act on other None
    if other is None:
      if self.arg is None: return  0
      else               : return -1

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
        if eval('float(self) %s other' % compare): return  0
        else                                     : return -1

    # act on None
    if self.arg is None:
      if type(other)==float: return  0
      else                 : return -1

    # compare to other values: class/float/int
    if   float(self) < float(other): return -1
    elif float(self) > float(other): return +1
    else                           : return  0


# ==============================================================================
# Time class: derived of the Unit class, and thus similar to Data
# ==============================================================================

class Time(Unit):
  r'''
Class to store time, and print in an easily readable format.

:argument/field:

  **arg** (``<int>`` | ``<float>`` | ``<str>``)
    The time as:

    * ``<float>``: number of seconds
    * ``<str>``  : time in clock format, "HH:MM:SS"
    * ``<str>``  : time in a single unit, e.g. "1m"

:print format:

  The print format may be of the following type::

    {:[align][width].[precision][type]}

  The *type* can be:

  * ``s`` or ``m`` (default) to print using the dominating unit (seconds,
    minutes, hours, days)
  * ``f`` or ``e`` to print the time as floating point in seconds

  Consider the following example::

    >>> gpbs.Time('10d')
    10d

    >>> '{:.1f}'.format(gpbs.Time('10d'))
    864000.0

    >>> '{:.1e}'.format(gpbs.Time('10d'))
    8.6e+05

    >>> '{:.1s}'.format(gpbs.Time('10d'))
    10.0d
  '''

  # ----------------------------------------------------------------------------
  # convert string (or float) to float [used in class constructor]
  # ----------------------------------------------------------------------------

  def str2float(self,arg):

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
    try   : return float(arg)
    except: raise IOError('Unknown input string "%s"' % arg)

  # ----------------------------------------------------------------------------
  # convert to string
  # ----------------------------------------------------------------------------

  def __format__(self,fmt):

    # print seconds as float (in different representations)
    if len(fmt)>0:
      if fmt[-1] in ['f','F','e','E']: return ('{:%s}'%fmt).format(float(self))
      if fmt[-1] in ['m','s'        ]: fmt = fmt[:-1]+'%'

    # break up print format in pieces / set default
    if len(fmt)>0: fmt = re.split('([><^=+-]?)([0-9]*)(\.?)([0-9]*)(.*)',fmt)
    else         : fmt = ['','','','','','','']

    # set defaults: misuse percent print to append unit
    fmt[-2] = '%'
    fmt[ 3] = '.'

    # set conversion factors (days,hours,minutes,seconds)
    ratio = {}
    ratio[60.0*60.0*24.0] = 'd'
    ratio[60.0*60.0     ] = 'h'
    ratio[60.0          ] = 'm'
    ratio[1.0           ] = 's'

    # set function to convert (print-format + unit + value) to string
    string = lambda fmt,unit,value: (('{:%s}'%''.join(fmt)).format(value/100.)).replace('%',unit)

    # loop over units from large to small, to print with unit
    for fac in sorted(ratio)[-1::-1]:
      if abs(float(self))>=fac:
        # print with default precision
        if len(fmt[4])>0:
          return string(fmt,ratio[fac],float(self)/fac)
        # no precision and no length: print with precision of one
        if len(fmt[2])==0:
          fmt[4] = '1'
          return string(fmt,ratio[fac],float(self)/fac)
        # fixed length: set precision to maximize the information
        fmt[4] = '1'
        text   = string(fmt,ratio[fac],float(self)/fac)
        if len(text)<=int(fmt[2]):
          return text
        else:
          fmt[4] = '0'
          return string(fmt,ratio[fac],float(self)/fac)

    # in all other cases: return empty string
    fmt[4] = '0'
    return ' '*len(string(fmt,'N',0.0))

# ==============================================================================
# Data class: derived of the Unit class, and thus similar to Time
# ==============================================================================

class Data(Unit):
  r'''
Class to store data, and print in an easily readable format.

:argument/field:

  **arg** (``<int>`` | ``<float>`` | ``<str>``)
    The data as number of bytes, or string:

    * ``<float>``: number of bytes
    * ``<str>``  : humanly readable string, e.g. "1gb"

:print format:

  The print format may be of the following type::

    {:[align][width].[precision][type]}

  The *type* can be:

  * ``s`` or ``m`` (default) to print using the dominating unit (kb,mb,gb,tb)
  * ``f`` or ``e`` to print the time as floating point in seconds

  Consider the following example::

    >>> gpbs.Data('10mb')
    10mb

    >>> '{:.1f}'.format(gpbs.Data('10mb'))
    10000000.0

    >>> '{:.1e}'.format(gpbs.Data('10mb'))
    1.0e+07

    >>> '{:.1s}'.format(gpbs.Data('10mb'))
    10.0mb
  '''

  # ----------------------------------------------------------------------------
  # convert string (or float) to float [used in class constructor]
  # ----------------------------------------------------------------------------

  def str2float(self,arg):

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
    try   : return float(arg)
    except: raise IOError('Unknown input string "%s"' % arg)

  # ----------------------------------------------------------------------------
  # convert to string
  # ----------------------------------------------------------------------------

  def __format__(self,fmt):

    # print seconds as float (in different representations)
    if len(fmt)>0:
      if fmt[-1] in ['f','F','e','E']: return ('{:%s}'%fmt).format(float(self))
      if fmt[-1] in ['m','s'        ]: fmt = fmt[:-1]+'%'

    # break up print format in pieces / set default
    if len(fmt)>0: fmt = re.split('([><^=+-]?)([0-9]*)(\.?)([0-9]*)(.*)',fmt)
    else         : fmt = ['','','','','','','']

    # set defaults: misuse percent print to append unit
    fmt[-2] = '%'
    fmt[ 3] = '.'
    if len(fmt[2])>0:
      fmt[2] = str(int(fmt[2])-1)

    # set conversion factors
    ratio = {}
    ratio[1.0e12] = 'tb'
    ratio[1.0e9 ] = 'gb'
    ratio[1.0e6 ] = 'mb'
    ratio[1.0e3 ] = 'kb'
    ratio[1.0e0 ] = 'b '

    # set function to convert (print-format + unit + value) to string
    string = lambda fmt,unit,value: (('{:%s}'%''.join(fmt)).format(value/100.)).replace('%',unit)

    # loop over units from large to small, to print with unit
    for fac in sorted(ratio)[-1::-1]:
      if abs(float(self))>=fac:
        # print with default precision
        if len(fmt[4])>0:
          return string(fmt,ratio[fac],float(self)/fac)
        # no precision and no length: print with precision of one
        if len(fmt[2])==0:
          fmt[4] = '0'
          return string(fmt,ratio[fac],float(self)/fac)
        # fixed length: set precision to maximize the information
        fmt[4] = '1'
        text   = string(fmt,ratio[fac],float(self)/fac)
        if len(text)<=int(fmt[2])+1:
          return text
        else:
          fmt[4] = '0'
          return string(fmt,ratio[fac],float(self)/fac)

    # in all other cases: return empty string
    fmt[4] = '0'
    return ' '*(len(string(fmt,'N',0.0))+1)

# ==============================================================================
# Custom float class
# ==============================================================================

class Float(Unit):
  r'''
Custom float class. Compared to the regular floats, this class can also be
``None``, such that the conversion to a string results in an empty string.

:argument/field:

  **arg** (``<float>`` | ``None``)
    The argument.

:print format:

  The print format may be of the following type::

    {:[align][width].[precision][type]}

  The output to a ``None`` argument is an empty string.
  '''

  # ----------------------------------------------------------------------------
  # class constructor
  # ----------------------------------------------------------------------------

  def __init__(self,arg):
    try   : self.arg = float(arg)
    except: self.arg = None

  # ----------------------------------------------------------------------------
  # formatted print
  # ----------------------------------------------------------------------------

  def __format__(self,fmt):

    fmt = '{:%s}'%fmt

    if self.arg is None:
      return ' '*len(fmt.format(0.0))
    else:
      return fmt.format(self.arg)

# ==============================================================================
# define color-schemes
# ==============================================================================
# ------------------------------------------------------------------------------
# default
# ------------------------------------------------------------------------------

class ColorDefault:
  r'''
Define default color scheme.

=========== ========================
Name        Style
=========== ========================
warning     red,bold
error       red,bold
selection   green,bold
down        red,strike-through
free        green,bold
end         end of style definition
=========== ========================

:custom:

  To create a custom color-scheme to the following::

    class ColorCustom:

      warning   = ''
      error     = ''
      selection = ''
      down      = ''
      free      = ''
      end       = ''

  whereby the string is used to specify the print format.
  See: `Wikipedia <https://en.wikipedia.org/wiki/ANSI_escape_code>`_
  '''

  warning   = '\033[1;31m'
  error     = '\033[1;31m'
  selection = '\033[1;32m'
  down      = '\033[9;31m'
  free      = '\033[1;32m'
  end       = '\033[0m'

# ------------------------------------------------------------------------------
# no colors
# ------------------------------------------------------------------------------

class ColorNone:
  r'''
Define scheme to print without color formatting.

=========== ========================
Name        Style
=========== ========================
warning     N/A
error       N/A
selection   N/A
down        N/A
free        N/A
end         N/A
=========== ========================
  '''

  warning   = ''
  error     = ''
  selection = ''
  down      = ''
  free      = ''
  end       = ''

# ==============================================================================
# parent class for Job/Node/Owner
# ==============================================================================

class Item(object):
  '''
Parent class for to provide common methods.
  '''

  # ----------------------------------------------------------------------------
  # print column header
  # ----------------------------------------------------------------------------

  def print_header(self,columns,fmt,ifs,trunc,line):
    r'''
Print the column header, including a separator line.

:arguments:

  **columns** ((``<dict>``,``<dict>``,...))
    A list with the print settings per column. For each column the print
    settings are given as dictionary, with the following fields:

    * ``key``   (mandatory): the name of the field (see class-constructor),
    * ``width`` (mandatory): the desired output-width,
    * ``head``  (mandatory): the header text,
    * ``color``            : the color-code (warning,error,selection,down,free).

    Note that if a color was specified, print the string using::

      print Item.print_header(...).format(color=gpbs.ColorDefault)
      print Item.print_header(...).format(color=gpbs.ColorNone   )

    or a custom-class (see: ``gpbs.ColorDefault``)

  **fmt** (``<dict>``)
    A dictionary with the print-format for each field. The ``width`` is
    replacement by the specified width.

    Example::

      fmt = {
        'example' : '>{width}.{width}s' ,
      }

  **ifs** (``<str>``)
    The column separator.

  **trunc** (``<str>``)
    The symbol to truncate columns that are printed narrower than their length.

  **line** (``<str>``)
    A symbol to form the separator line, for example ``'-'``
    '''

    # initiate output as list, combined to lines of text below
    output = []

    # loop over the columns set as argument
    for column in columns:
      # read the field name, and apply print format
      key  = column['key']
      text = ('{:'+fmt[key].format(**column)+'}').format(column['head'])
      # if the column is shorter than the information: add a truncation symbol
      if len(text)<len(self[key]):
        text = text[:-len(trunc)]+trunc
      # add color
      if 'color' in column:
        text = '{color.'+column['color']+'}'+text+'{color.end}'
      # add column to output
      output += [text]

    # return the line as text
    head = ifs.join(output)

    if len(line)==0:
      return head

    # initiate output at list, combined to line of text below
    output = []

    # loop over the columns set as argument
    for column in columns:
      # read the field name, and apply print format
      key  = column['key']
      text = ('{:'+fmt[key].format(**column)+'}').format(line*200)
      # add column to output
      output += [text]

    return head+'\n'+ifs.join(output)

  # ----------------------------------------------------------------------------
  # print in columns
  # ----------------------------------------------------------------------------

  def print_column(self,columns,fmt,ifs,trunc):
    r'''
Print data in columns.

:arguments:

  **columns** (``(<dict>,<dict>,...)``)
    A list with the print settings per column. For each column the print
    settings are given as dictionary, with the following fields:

    * ``key``   (mandatory): the name of the field (see class-constructor),
    * ``width`` (mandatory): the desired output-width,
    * ``color``            : the color-code (warning,error,selection,down,free).

    Note that if a color was specified, print the string using::

      print Item.print_column(...).format(color=gpbs.ColorDefault)
      print Item.print_column(...).format(color=gpbs.ColorNone   )

    or a custom-class (see: ``gpbs.ColorDefault``)

  **fmt** (``<dict>``)
    A dictionary with the print-format for each field. The ``width`` is
    replacement by the specified width.

    Example::

      fmt = {
        'example' : '>{width}.{width}s' ,
      }

  **ifs** (``<str>``)
    The column separator.

  **trunc** (``<str>``)
    The symbol to truncate columns that are printed narrower than their length.
    '''

    # initiate output at list, combined to line of text below
    output = []

    # loop over the columns set as argument
    for column in columns:
      # read the field name, and apply print format
      key  = column['key']
      text = ('{:'+fmt[key].format(**column)+'}').format(getattr(self,key))
      # if the column is shorter than the information: add a truncation symbol
      if len(text)<len(self[key]):
        text = text[:-len(trunc)]+trunc
      # add color
      if 'color' in column:
        if column['color']:
          text = '{color.'+column['color']+'}'+text+'{color.end}'
      # add column to output
      output += [text]

    # return the line as text
    return ifs.join(output)


# ==============================================================================
# class to store an individual job
# ==============================================================================

class Job(Item):
  r'''
Class to store the job information. The data is stored as fields of this class.
If the class is reference as index, a string is returned in a common print
format. I.e.::

  >>> type(job.cputime)
  <class 'gpbs.Time'>

  >>> type(job['cputime'])
  <str>

For example::

  >>> float(job.cputime)
  1000.0

  >>> job['cputime']
  17m

:arguments:

  **text** (``<str>``) *optional*
    The output of the `qstat -f` command for this job. I.e.::

      text << `qstat -f`
      Job(text.split(Job Id:))

:options/fields:

  **id** (``<str>``)
    ID (as string).

  **name** (``<str>``)
    Name, as specified by the ``-N`` option.

  **owner** (``<str>``)
    Owner (username).

  **state** (``<str>``)
    Status of the job (R=running, Q=queued, E=exiting).

  **resnode** (``<gpbs.ResNode>``)
    Claimed nodes/CPUs.

  **cputime** (``<gpbs.Time>``)
    Time that the job has been using CPU resources.

  **walltime** (``<gpbs.Time>``)
    Time that the job has been running.

  **host** (``<gpbs.Host>``)
    Host that is running the job.

  **memused** (``<gpbs.Data>``)
    Memory used by the job.

  **pmem** (``<gpbs.Data>``)
    Specified ``pmem`` qsub-option.

  **score** (``<gpbs.Float>``)
    Score: ``cputime / walltime``.

  **submit_args** (``<str>``)
    The arguments that were given to the ``qsub`` command: the filename and the
    options.
  '''

  # ----------------------------------------------------------------------------
  # class constructor
  # ----------------------------------------------------------------------------

  def __init__(self,*args,**kwargs):

    # check number of input arguments
    if len(args)>1:
      raise IOError('Unknown number of input arguments')

    # (a) read input text
    if len(args)==1:
      # name alias
      text = args[0]
      # split/convert the different parts
      self.id          = text.split('\n')[0].split('.')[0].strip()
      self.name        = csplit(text,'Job_Name'                               )
      self.owner       = csplit(text,'Job_Owner'                              ).split('@')[0]
      self.state       = csplit(text,'job_state'                              )
      self.resnode     = csplit(text,'Resource_List.nodes'    ,dtype='ResNode')
      self.pmem        = csplit(text,'Resource_List.pmem'     ,dtype='Data'   )
      self.memused     = csplit(text,'resources_used.mem'     ,dtype='Data'   )
      self.cputime     = csplit(text,'resources_used.cput'    ,dtype='Time'   )
      self.walltime    = csplit(text,'resources_used.walltime',dtype='Time'   )
      self.host        = csplit(text,'exec_host'              ,dtype='Host'   )
      self.submit_args = csplit(text,'submit_args'                            )
      self.output_path = csplit(text,'Output_Path'                            )

    # (b) store from input (overwrites read data)
    for key in kwargs:
      setattr(self,key,kwargs[key])

    # calculate the job's score
    if not hasattr(self,'score'):
      try:
        self.score = Float(float(self.cputime)/(float(self.walltime)*float(len(self.host))))
      except:
        self.score = Float(None)

  # ----------------------------------------------------------------------------
  # print to screen
  # ----------------------------------------------------------------------------

  def __repr__(self):
    return self.__str__()

  def __str__(self):
    return self['id']

  # ----------------------------------------------------------------------------
  # reference as dictionary: return as string
  # ----------------------------------------------------------------------------

  def __getitem__(self,key):

    fmt = {
      'id'          : '{:s}'    ,
      'owner'       : '{:s}'    ,
      'resnode'     : '{:s}'    ,
      'state'       : '{:s}'    ,
      'pmem'        : '{:.0s}'  ,
      'memused'     : '{:.0s}'  ,
      'cputime'     : '{:4s}'   ,
      'walltime'    : '{:4s}'   ,
      'host'        : '{:s}'    ,
      'score'       : '{:>4.2f}',
      'name'        : '{:s}'    ,
      'submit_args' : '{:s}'    ,
      'output_path' : '{:s}'    ,
    }

    return fmt[key].format(getattr(self,key))

  # ----------------------------------------------------------------------------
  # print in columns
  # ----------------------------------------------------------------------------

  def print_column(self,columns,ifs='  ',trunc='...'):
    r'''
Print job in columns.

:arguments:

  **columns** (``(<dict>,<dict>,...)``)
    A list with the print settings per column. For each column the print
    settings are given as dictionary, with the following fields:

    * ``key``   (mandatory): the name of the field (see class-constructor),
    * ``width`` (mandatory): the desired output-width,
    * ``color``            : the color-code (warning,error,selection,down,free).

    Note that if a color was specified, print the string using::

      print Job.print_column(...).format(color=gpbs.ColorDefault)
      print Job.print_column(...).format(color=gpbs.ColorNone   )

    or a custom-class (see: ``gpbs.ColorDefault``)

:options:

  **ifs** ([``'  '``] | ``<str>``)
    The column separator.

  **trunc** ([``...``] | ``<str>``)
    The symbol to truncate columns that are printed narrower than their length.
    '''

    # get keys in column
    keys = {col['key']:icol for icol,col in enumerate(columns)}

    # make a copy of "columns", to be able to overwrite stuff
    columns_c = [{} for col in columns]
    for icol,col in enumerate(columns):
      columns_c[icol] = {key:col[key] for key in col}

    # provide warnings (overwrite color)
    if ( self.memused>'1gb' and self.pmem==None ) and 'memused' in keys: columns_c[keys['memused']]['color'] = 'warning'
    if ( self.score>1.03    or  self.score<0.95 ) and 'score'   in keys: columns_c[keys['score'  ]]['color'] = 'warning'

    # print format per available field
    fmt = {
      'id'          : '>{width}.{width}s' ,
      'owner'       : '<{width}.{width}s' ,
      'resnode'     : '>{width}.{width}s' ,
      'state'       : '>{width}.{width}s' ,
      'pmem'        : '>{width}.0s'       ,
      'memused'     : '>{width}.0s'       ,
      'cputime'     : '>{width}s'         ,
      'walltime'    : '>{width}s'         ,
      'host'        : '>{width}.{width}s' ,
      'score'       : '>{width}.2f'       ,
      'name'        : '<{width}.{width}s' ,
      'submit_args' : '<{width}.{width}s' ,
    }

    # print using parent 'Item' class
    return super(Job,self).print_column(columns_c,fmt,ifs,trunc)

  # ----------------------------------------------------------------------------
  # print column header
  # ----------------------------------------------------------------------------

  def print_header(self,columns,ifs='  ',trunc='...',line='-'):
    r'''
Print column headers, and a header separator line.

:arguments:

  **columns** (``(<dict>,<dict>,...)``)
    A list with the print settings per column. For each column the print
    settings are given as dictionary, with the following fields:

    * ``key``   (mandatory): the name of the field (see class-constructor),
    * ``width`` (mandatory): the desired output-width,
    * ``head``  (mandatory): the header text,
    * ``color``            : the color of the column (see ``<gpbs.Color>``).

    Note that if a color was specified, print the string using::

      print Job.print_header(...).format(color=gpbs.ColorDefault)
      print Job.print_header(...).format(color=gpbs.ColorNone   )

    or a custom-class (see: ``gpbs.ColorDefault``)

:options:

  **ifs** ([``'  '``] | ``<str>``)
    The column separator.

  **trunc** ([``...``] | ``<str>``)
    The symbol to truncate columns that are printed narrower than their length.

  **line** ([``'-'``] | ``<str>``)
    Symbol that forms the separator line.
    '''

    # print format per available field
    fmt = {
      'id'          : '<{width}.{width}s' ,
      'owner'       : '<{width}.{width}s' ,
      'resnode'     : '<{width}.{width}s' ,
      'state'       : '<{width}.{width}s' ,
      'pmem'        : '<{width}.{width}s' ,
      'memused'     : '<{width}.{width}s' ,
      'cputime'     : '<{width}.{width}s' ,
      'walltime'    : '<{width}.{width}s' ,
      'host'        : '<{width}.{width}s' ,
      'score'       : '<{width}.{width}s' ,
      'name'        : '<{width}.{width}s' ,
      'submit_args' : '<{width}.{width}s' ,
    }

    # print using parent 'Item' class
    return super(Job,self).print_header(columns,fmt,ifs,trunc,line)

# ==============================================================================
# compute node information
# ==============================================================================

class Node(Item):
  r'''
Class to store the node information. The data is stored as fields of this class.
If the class is reference as index, a string is returned in a common print
format. I.e.::

  >>> type(node.memt)
  <class 'gpbs.Data'>

  >>> type(node['memt'])
  <str>

For example::

  >>> float(node.memt)
  1000.0

  >>> node['memt']
  1kb

:arguments:

  text (``<str>``) *optional*
    The output of the `pbsnodes` command for this node. I.e.::

      text << `qpbsnodes`
      Node(text.split('\\n\\n'))

:options/fields:

  **name** (``<str>``)
    Name of the compute-node.

  **node** (``<int>``), *calculated*
    Node number (``compute-0-X -> int(X)``)

  **state** (``<str>``)
    Status (free,job-exclusive,down,offline).

  **ncpu** (``<int>``)
    Number of CPUs present in the node.

  **cpufree** (``<int>``), *calculated*
    Number of free CPUs.

  **ctype** (``<str>``)
    Type of node (intel,amd).

  **jobs** (``<list>``)
    List of job-ids.

  **memt** (``<gpbs.Data>``)
    Total memory.

  **mema** (``<gpbs.Data>``)
    Available memory.

  **memu** (``<gpbs.Data>``), *calculated*
    Memory in use.

  **memp** (``<gpbs.Data>``)
    Physical memory.

  **relmemu** (``<gpbs.Float>``)
    Percentage of memory used.

  **load** (``<gpbs.Float>``)
    The load of the node, defined as
    :math:`0 \leq \mathrm{load} \leq n_\mathrm{cpu}`.

  **score** (``<gpbs.Float>``), *calculated*
    The relative CPU usage by the jobs: ``load / len(jobs)``

  **disk_total** (``<gpbs.Data>``)
    Total disk space.

  **disk_free** (``<gpbs.Data>``)
    Free disk space.

  **reldisku** (``<gpbs.Float>``)
    Percentage of disk space used.

  **bytes_in** (``<gpbs.Data>``)
    Network traffic in-bound.

  **bytes_out** (``<gpbs.Data>``)
    Network traffic out-bound.

  **bytes_total** (``<gpbs.Data>``)
    Total network traffic.

  **cpu_idle** (``<gpbs.Float>``)
    CPU idle (waiting) percentage.
  '''

  # ----------------------------------------------------------------------------
  # class constructor
  # ----------------------------------------------------------------------------

  def __init__(self,*args,**kwargs):

    # support functions
    # -----------------

    # support function, split jobs: 0/X.hostname
    def jsplit(txt):
      try:
        jobs = txt.split('jobs =')[1].split('\n')[0].strip().split(',')
        return [int(i.split('/')[1].split('.')[0].strip()) for i in jobs]
      except:
        return []

    # set function to convert GB to B
    giga = lambda x: None if x is None else float(x)*1.0e9

    # read input
    # ----------

    # check number of input arguments
    if len(args)>1:
      raise IOError('Unknown number of input arguments')

    # (a) read ganglia output
    self.disk_total = Data( giga( kwargs.pop( 'disk_total' , None ) ) )
    self.disk_free  = Data( giga( kwargs.pop( 'disk_free'  , None ) ) )
    self.bytes_in   = Data(       kwargs.pop( 'bytes_in'   , None )   )
    self.bytes_out  = Data(       kwargs.pop( 'bytes_out'  , None )   )
    self.cpu_idle   = Float(      kwargs.pop( 'cpu_idle'   , None )   )

    # (b) read input string to pbsnodes command
    if len(args)==1:
      # alias the input text
      text = args[0]
      # read different fields
      self.name  = text.split('\n')[0]
      self.state = csplit(text,'state'                                     )
      self.ncpu  = csplit(text,'np'                          ,dtype='int'  )
      self.ctype = csplit(text,'properties'                                )
      self.jobs  = jsplit(text                                             )
      self.memt  = csplit(text,'totmem'  ,postfix='=',ifs=',',dtype='Data' )
      self.memp  = csplit(text,'physmem' ,postfix='=',ifs=',',dtype='Data' )
      self.mema  = csplit(text,'availmem',postfix='=',ifs=',',dtype='Data' )
      self.load  = csplit(text,'loadave' ,postfix='=',ifs=',',dtype='Float')

    # (c) copy from input (overwrites input from the pbsnodes command)
    for key in kwargs:
      setattr(self,key,kwargs.pop(key))

    # set default
    if self.jobs is None:
      self.jobs = []

    # calculate extra fields
    # ----------------------

    # derive memory, disk, network
    self.memu      = self.memt       -     self.mema
    self.bytes_tot = self.bytes_in   +     self.bytes_out
    self.disk_used = self.disk_total -     self.disk_free
    self.cpufree   = self.ncpu       - len(self.jobs)

    # score: the average load per running job
    if len(self.jobs)>0:
      self.score = Float(self.load/len(self.jobs))
    else:
      self.score = 1.0

    # percentage of memory used
    try:
      self.relmemu = Float(self.memu/self.memt)
    except:
      self.relmemu = Float(None)

    # percentage of disk space used
    try:
      self.reldisku = Float(self.disk_used/self.disk_total)
    except:
      self.reldisku = Float(None)

    # node number as integer
    try:
      self.node = int(self.name.replace('compute-0-',''))
    except:
      self.node = None

    # remove information for offline nodes
    if self.state in ['offline','down','down,job-exclusive']:
      self.cpufree   = 0
      self.bytes_tot = Data(None)
      self.memu      = Data(None)

  # ----------------------------------------------------------------------------
  # print to screen
  # ----------------------------------------------------------------------------

  def __repr__(self):
    return self.__str__()

  def __str__(self):
    return self['node']

  # ----------------------------------------------------------------------------
  # reference as dictionary: return as string
  # ----------------------------------------------------------------------------

  def __getitem__(self,key):

    fmt = {
      'node'        : '{:d}'    ,
      'name'        : '{:s}'    ,
      'state'       : '{:s}'    ,
      'ncpu'        : '{:d}'    ,
      'cpufree'     : '{:d}'    ,
      'ctype'       : '{:s}'    ,
      'jobs'        : '{:s}'    ,
      'memt'        : '{:.0s}'  ,
      'memp'        : '{:.0s}'  ,
      'mema'        : '{:.0s}'  ,
      'memu'        : '{:.0s}'  ,
      'relmemu'     : '{:4.2f}' ,
      'disk_total'  : '{:.0s}'  ,
      'disk_free'   : '{:.0s}'  ,
      'reldisku'    : '{:4.2f}' ,
      'bytes_in'    : '{:.0s}'  ,
      'bytes_out'   : '{:.0s}'  ,
      'bytes_tot'   : '{:.0s}'  ,
      'load'        : '{:4.2f}' ,
      'score'       : '{:4.2f}' ,
      'cpu_idle'    : '{:4.1f}' ,
    }

    return fmt[key].format(getattr(self,key))

  # ----------------------------------------------------------------------------
  # print in columns
  # ----------------------------------------------------------------------------

  def print_column(self,columns,ifs='  ',trunc='...'):
    r'''
Function used to print nodes in columns.

:arguments:

  **columns** (``(<dict>,<dict>,...)``)
    A list with the print settings per column. For each column the print
    settings are given as dictionary, with the following fields:

    * ``key``   (mandatory): the name of the field (see class-constructor),
    * ``width`` (mandatory): the desired output-width,
    * ``color``            : the color-code (warning,error,selection,down,free).

    Note that if a color was specified, print the string using::

      print Node.print_column(...).format(color=gpbs.ColorDefault)
      print Node.print_column(...).format(color=gpbs.ColorNone   )

    or a custom-class (see: ``gpbs.ColorDefault``)

:options:

  **ifs** ([``'  '``] | ``<str>``)
    The column separator.

  **trunc** ([``...``] | ``<str>``)
    The symbol to truncate columns that are printed narrower than their length.
    '''

    # get keys in column
    keys = {col['key']:icol for icol,col in enumerate(columns)}

    # make a copy of "columns", to be able to overwrite stuff
    columns_c = [{} for col in columns]
    for icol,col in enumerate(columns):
      columns_c[icol] = {key:col[key] for key in col}

    # provide warnings (overwrite color)
    if ( self.relmemu  > 0.8                       ) and 'memu'      in keys: columns_c[keys['memu'     ]]['color'] = 'warning'
    if ( self.relmemu  > 0.8                       ) and 'relmemu'   in keys: columns_c[keys['relmemu'  ]]['color'] = 'warning'
    if ( self.reldisku > 0.7                       ) and 'disk_free' in keys: columns_c[keys['disk_free']]['color'] = 'warning'
    if ( self.reldisku > 0.7                       ) and 'reldisku'  in keys: columns_c[keys['reldisku' ]]['color'] = 'warning'
    if ( self.cpufree  > 0                         ) and 'cpufree'   in keys: columns_c[keys['cpufree'  ]]['color'] = 'free'
    if ( self.score    > 1.05 or self.score < 0.95 ) and 'score'     in keys: columns_c[keys['score'    ]]['color'] = 'warning'

    # show not-running node different (overwrite color)
    if self.state not in ['free','job-exclusive']:
      for key in keys:
        columns_c[keys[key]]['color'] = 'down'

    # print format per available field
    fmt = {
      'node'        : '>{width}d'         ,
      'name'        : '<{width}.{width}s' ,
      'state'       : '<{width}.{width}s' ,
      'ncpu'        : '>{width}d'         ,
      'cpufree'     : '>{width}d'         ,
      'ctype'       : '<{width}.{width}s' ,
      'jobs'        : '<{width}.{width}s' ,
      'memt'        : '>{width}.0s'       ,
      'memp'        : '>{width}.0s'       ,
      'mema'        : '>{width}.0s'       ,
      'memu'        : '>{width}.0s'       ,
      'relmemu'     : '>{width}.2f'       ,
      'disk_total'  : '>{width}.0s'       ,
      'disk_free'   : '>{width}.0s'       ,
      'reldisku'    : '>{width}.2f'       ,
      'bytes_in'    : '>{width}.0s'       ,
      'bytes_out'   : '>{width}.0s'       ,
      'bytes_tot'   : '>{width}.0s'       ,
      'load'        : '>{width}.2f'       ,
      'score'       : '>{width}.2f'       ,
      'cpu_idle'    : '>{width}.1f'       ,
    }

    # print using parent 'Item' class
    return super(Node,self).print_column(columns_c,fmt,ifs,trunc)

  # ----------------------------------------------------------------------------
  # print column header
  # ----------------------------------------------------------------------------

  def print_header(self,columns,ifs='  ',trunc='...',line='-'):
    r'''
Print column headers, and a header separator line.

:arguments:

  **columns** (``(<dict>,<dict>,...)``)
    A list with the print settings per column. For each column the print
    settings are given as dictionary, with the following fields:

    * ``key``   (mandatory): the name of the field (see class-constructor),
    * ``width`` (mandatory): the desired output-width,
    * ``head``  (mandatory): the header text,
    * ``color``            : the color of the column (see ``<gpbs.Color>``).

    Note that if a color was specified, print the string using::

      print Node.print_header(...).format(color=gpbs.ColorDefault)
      print Node.print_header(...).format(color=gpbs.ColorNone   )

    or a custom-class (see: ``gpbs.ColorDefault``)

:options:

  **ifs** ([``'  '``] | ``<str>``)
    The column separator.

  **trunc** ([``...``] | ``<str>``)
    The symbol to truncate columns that are printed narrower than their length.

  **line** ([``'-'``] | ``<str>``)
    Symbol that forms the separator line.
    '''

    fmt = {
      'node'        : '<{width}.{width}s' ,
      'name'        : '<{width}.{width}s' ,
      'state'       : '<{width}.{width}s' ,
      'ncpu'        : '<{width}.{width}s' ,
      'cpufree'     : '<{width}.{width}s' ,
      'ctype'       : '<{width}.{width}s' ,
      'jobs'        : '<{width}.{width}s' ,
      'memt'        : '<{width}.{width}s' ,
      'memp'        : '<{width}.{width}s' ,
      'mema'        : '<{width}.{width}s' ,
      'memu'        : '<{width}.{width}s' ,
      'relmemu'     : '<{width}.{width}s' ,
      'disk_total'  : '<{width}.{width}s' ,
      'disk_free'   : '<{width}.{width}s' ,
      'reldisku'    : '<{width}.{width}s' ,
      'bytes_in'    : '<{width}.{width}s' ,
      'bytes_out'   : '<{width}.{width}s' ,
      'bytes_tot'   : '<{width}.{width}s' ,
      'load'        : '<{width}.{width}s' ,
      'score'       : '<{width}.{width}s' ,
      'cpu_idle'    : '<{width}.{width}s' ,
    }

    # print using parent 'Item' class
    return super(Node,self).print_header(columns,fmt,ifs,trunc,line)

# ==============================================================================
# class to store user summary
# ==============================================================================

class Owner(Item):
  r'''
Class to store and print total resources per owner.

:options/fields:

  **owner** (``<str>``)
    Owner (username).

  **cpus** (``<int>``)
    Claimed CPUs.

  **memused** (``<gpbs.Data>``)
    Memory used by the owner's jobs.

  **walltime** (``<gpbs.Time>``)
    Time that the jobs have been running.

  **claimtime** (``<gpbs.Time>``)
    The total walltime multiplied by the number of CPUs (per individual job).

  **cputime** (``<gpbs.Time>``)
    Time that the jobs have been using CPU resources.
  '''

  # ----------------------------------------------------------------------------
  # class constructor
  # ----------------------------------------------------------------------------

  def __init__(self,**kwargs):

    self.owner     = kwargs.pop( 'owner'                   )
    self.cpus      = kwargs.pop( 'cpus'      , 0           )
    self.memused   = kwargs.pop( 'memused'   , Data(0.0)   )
    self.walltime  = kwargs.pop( 'walltime'  , Time(0.0)   )
    self.claimtime = kwargs.pop( 'claimtime' , Time(0.0)   )
    self.cputime   = kwargs.pop( 'cputime'   , Time(0.0)   )

    try:
      self.score = Float(float(self.cputime)/float(self.claimtime))
    except:
      self.score = Float(None)

  # ----------------------------------------------------------------------------
  # print to screen
  # ----------------------------------------------------------------------------

  def __repr__(self):
    return self.__str__()

  def __str__(self):
    return self['owner']

  # ----------------------------------------------------------------------------
  # reference as dictionary: return as string
  # ----------------------------------------------------------------------------

  def __getitem__(self,key):

    fmt = {
      'owner'       : '{:s}'    ,
      'cpus'        : '{:d}'    ,
      'memused'     : '{:5.0s}' ,
      'walltime'    : '{:4.0s}' ,
      'cputime'     : '{:4.0s}' ,
      'claimtime'   : '{:4.0s}' ,
      'score'       : '{:4.2f}' ,
    }

    return fmt[key].format(getattr(self,key))

  # ----------------------------------------------------------------------------
  # print in columns
  # ----------------------------------------------------------------------------

  def print_column(self,columns,ifs='  ',trunc='...'):
    r'''
Print user-summary in columns.

:arguments:

  **columns** (``(<dict>,<dict>,...)``)
    A list with the print settings per column. For each column the print
    settings are given as dictionary, with the following fields:

    * ``key``   (mandatory): the name of the field (see class-constructor),
    * ``width`` (mandatory): the desired output-width,
    * ``color``            : the color-code (warning,error,selection,down,free).

    Note that if a color was specified, print the string using::

      print Owner.print_column(...).format(color=gpbs.ColorDefault)
      print Owner.print_column(...).format(color=gpbs.ColorNone   )

    or a custom-class (see: ``gpbs.ColorDefault``)

:options:

  **ifs** ([``'  '``] | ``<str>``)
    The column separator.

  **trunc** ([``...``] | ``<str>``)
    The symbol to truncate columns that are printed narrower than their length.
    '''

    # get keys in column
    keys = {col['key']:icol for icol,col in enumerate(columns)}

    # make a copy of "columns", to be able to overwrite stuff
    columns_c = [{} for col in columns]
    for icol,col in enumerate(columns):
      columns_c[icol] = {key:col[key] for key in col}

    # provide warnings (overwrite color)
    if ( self.score>1.03 or self.score<0.95 ) and 'score' in keys: columns_c[keys['score'  ]]['color'] = 'warning'

    # print format per available field
    fmt = {
      'owner'       : '<{width}.{width}s' ,
      'cpus'        : '>{width}d'         ,
      'memused'     : '>{width}.0s'       ,
      'walltime'    : '>{width}.0s'       ,
      'cputime'     : '>{width}.0s'       ,
      'claimtime'   : '>{width}.0s'       ,
      'score'       : '>{width}.2f'       ,
    }

    # print using parent 'Item' class
    return super(Owner,self).print_column(columns_c,fmt,ifs,trunc)

  # ----------------------------------------------------------------------------
  # print column header
  # ----------------------------------------------------------------------------

  def print_header(self,columns,ifs='  ',trunc='...',line='-'):
    r'''
Print column headers, and a header separator line.

:arguments:

  **columns** (``(<dict>,<dict>,...)``)
    A list with the print settings per column. For each column the print
    settings are given as dictionary, with the following fields:

    * ``key``   (mandatory): the name of the field (see class-constructor),
    * ``width`` (mandatory): the desired output-width,
    * ``head``  (mandatory): the header text,
    * ``color``            : the color of the column (see ``<gpbs.Color>``).

    Note that if a color was specified, print the string using::

      print Owner.print_header(...).format(color=gpbs.ColorDefault)
      print Owner.print_header(...).format(color=gpbs.ColorNone   )

    or a custom-class (see: ``gpbs.ColorDefault``)

:options:

  **ifs** ([``'  '``] | ``<str>``)
    The column separator.

  **trunc** ([``...``] | ``<str>``)
    The symbol to truncate columns that are printed narrower than their length.

  **line** ([``'-'``] | ``<str>``)
    Symbol that forms the separator line.
    '''
    fmt = {
      'owner'       : '<{width}.{width}s' ,
      'cpus'        : '<{width}.{width}s' ,
      'memused'     : '<{width}.{width}s' ,
      'walltime'    : '<{width}.{width}s' ,
      'cputime'     : '<{width}.{width}s' ,
      'claimtime'   : '<{width}.{width}s' ,
      'score'       : '<{width}.{width}s' ,
    }

    # print using parent 'Item' class
    return super(Owner,self).print_header(columns,fmt,ifs,trunc,line)

# ==============================================================================
# support function to split text
# ==============================================================================

def csplit(text,name,postfix=' =',ifs='\n',dtype=None,default=''):
  r'''
Split a string, and convert to a specific data type.

:arguments:

  **text** (``<str>``)
    String to split/convert.

  **name** (``<str>``)
    Key-name, at which to split the string (in front of the data).

:options:

  **postfix** ([``' ='``] | ``<str>``)
    Post-fix of the key-name (in front of the data).

  **ifs** ([``'\n'``] | ``<str>``)
    Separator (after the data).

  **dtype** ([``None``] | ``<int>`` | ... | ``<Data>`` | ...)
    Data-type to which to convert the data.

:returns:

  **data** ([``<str>``] | ...)
    Data read (and converted to a specific data-type).

:example:

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
    text = re.sub(' +',' ',text).strip().split(name+postfix)[1].split(ifs)[0].strip()
  except:
    text = default

  # convert the data-type
  if dtype is not None:
    return eval('%s(text)'%dtype)
  else:
    return text

# ##############################################################################
# -------------------- PART 2 - READ/PRINT QSTAT/PBSNODES ---------------------
# ##############################################################################

# ==============================================================================
# read
# ==============================================================================

class Read:

  # ----------------------------------------------------------------------------
  # ``qstat -f`` -> list of Job
  # ----------------------------------------------------------------------------

  @staticmethod
  def myqstat():
    r'''
Read the output of the ``qstat -f`` command.

.. note::

  If the ``qstat -f`` command fails the function tries to run in debug mode
  by reading the output from a file ``qstat.log``. A notification is printed
  that the function runs in debug mode.

:returns:

  **jobs** (``<list>``)
    A list with jobs of the ``<gpbs.Job>``-class.
    '''

    # read qstat
    # ----------

    # read command
    import commands
    (stat,qstat) = commands.getstatusoutput('/opt/torque/bin/qstat -f')

    # command failed, try to run in debug mode
    if stat:
      if os.path.isfile('qstat.log'):
        print('\nRunning in debug mode\n')
        qstat = open('qstat.log','r').read()
      else:
        raise IOError('''
          ``qstat -f`` command failed.\n
          To run in debug mode, place the output of the ``qstat -f`` command in
          a file ``qstat.log`` in the same folder as the gpbs-module. Use::

            $ qstat -f > qstat.log
        ''')

    # convert to list of jobs
    # -----------------------

    # replace hard word-wrap, and split in jobs
    jobs = qstat.replace('\n\t','')
    jobs = jobs.split('Job Id:')[1:]

    # read/convert each job
    for (ijob,job) in enumerate(jobs):
      jobs[ijob] = Job(job)

    return jobs

  # ----------------------------------------------------------------------------
  # ``qstat -f`` -> list of Owner
  # ----------------------------------------------------------------------------

  @staticmethod
  def myqstat_user():
    r'''
Summary per user.

.. note::

  If the ``qstat -f`` command fails the function tries to run in debug mode
  by reading the output from a file ``qstat.log``. A notification is printed
  that the function runs in debug mode.

:returns:

  **owners** (``<list>``)
    A list with user summary of the ``<gpbs.Owner>``-class.
    '''

    # read all jobs
    jobs = Read.myqstat()

    # list all owners that are running jobs
    owners = set([job.owner for job in jobs])

    # initiate output
    summary = []

    # calculate total resources per user
    for owner in owners:
      # list with all the owner's jobs
      user = [job for job in jobs if job.owner==owner]
      # add to summary list
      summary.append(Owner(
        owner     = owner,
        cpus      = sum([job.host                                       for job in user]),
        memused   = sum([job.memused                                    for job in user]),
        walltime  = sum([job.walltime                                   for job in user]),
        cputime   = sum([job.cputime                                    for job in user]),
        claimtime = sum([Time(float(job.walltime)*float(len(job.host))) for job in user]),
      ))

    return sorted(summary,key=lambda owner: owner.cpus)

  # ----------------------------------------------------------------------------
  # ``pbsnodes`` / ``ganglia`` -> list of Node
  # ----------------------------------------------------------------------------

  @staticmethod
  def myqstat_node(ganglia=False):
    r'''
Read the output of the ``pbsnodes`` (and the ``ganglia``) command.

.. note::

  If the ``pbsnodes`` command fails the function tries to run in debug mode
  by reading the output from a file ``pbsnodes.log``. A notification is printed
  that the function runs in debug mode. Likewise for the ``ganglia`` command,
  the file ``ganglia.log`` is used.

:options:

  **ganglia** ([``False``] | ``True``)
    If set ``False`` the ``ganglia`` command is not read.

:returns:

  nodes (``<list>``)
    A list with compute-nodes of the ``<gpbs.Node>``-class.
    '''

    debug = False

    # read ``pbsnodes``
    # -----------------

    # read command
    import commands
    (stat,pbsnodes) = commands.getstatusoutput('/opt/torque/bin/pbsnodes')

    # command failed, run in debug mode
    if stat:
      if os.path.isfile('pbsnodes.log'):
        print('\nRunning in debug mode\n')
        pbsnodes = open('pbsnodes.log','r').read()
        debug    = True
      else:
        raise IOError('''
          ``pbsnodes`` command failed.\n
          To run in debug mode, place the output of the ``pbsnodes`` command in
          a file ``pbsnodes.log`` in the same folder as the gpbs-module. Use::

            $ pbsnodes > pbsnodes.log
        ''')

    # split the ``pbsnodes`` output in different nodes
    pbsnodes = filter(None,pbsnodes.split('\n\n'))

    # return list of nodes
    if not ganglia:

      for (ipbs,pbs) in enumerate(pbsnodes):
        pbsnodes[ipbs] = Node(pbs)

      return pbsnodes

    # read ``ganglia``
    # ----------------

    # initiate the ganglia options, and the output
    args = ['disk_total','disk_free','bytes_in','bytes_out','cpu_idle']
    dat  = {pbs.split('\n')[0]:{} for pbs in pbsnodes}

    # read command
    if not debug:

      import commands
      (stat,ganglia) = commands.getstatusoutput('ganglia '+' '.join(args))

    else:

      if os.path.isfile('ganglia.log'):
        ganglia = open('ganglia.log','r').read()
      else:
        raise IOError('''
          ``ganglia`` command failed.\n
          To run in debug mode, place the output of the ``ganglia`` command in
          a file ``ganglia.log`` in the same folder as the gpbs-module. Use::

            $ ganglia disk_total disk_free bytes_in bytes_out cpu_idle > ganglia.log
        ''')

    # loop over lines: split lines and store in dictionary per node
    for line in ganglia.split('\n'):
      try:
        out        = filter(None,line.replace("\t","").split(" "))
        (name,out) = (out[0],out[1:])
        dat[name]  = {arg:out[i] for (i,arg) in enumerate(args)}
      except:
        pass

    # change name
    ganglia = dat

    # loop over pbs-output (nodes) and convert to Node class
    for (ipbs,pbs) in enumerate(pbsnodes):
      pbsnodes[ipbs] = Node(pbs,**ganglia[pbs.split('\n')[0]])

    return pbsnodes

# ==============================================================================
# print
# ==============================================================================

class Print:

  # ----------------------------------------------------------------------------
  # support function: prompt user confirmation
  # ----------------------------------------------------------------------------

  @staticmethod
  def confirm(message='Proceed\ny/n?\n'):
    '''
Prompt the user for confirmation.

:option:

  **message** (``<str>``)
    Message to prompt.

:return:

  **response** (``True`` | ``False``)
    The user's answer.
  '''

    while True:

      user = raw_input(message)

      if not user                     : print 'Please enter y or n.'; continue
      if user not in ['y','Y','n','N']: print 'Please enter y or n.'; continue
      if user     in ['y','Y'        ]: return True
      if user     in ['n','N'        ]: return False

  # ----------------------------------------------------------------------------
  # support function: read the terminal size
  # ----------------------------------------------------------------------------

  @staticmethod
  def getTerminalSize():
    r'''
Get the size of the terminal.

:returns:

  lines (``<int>``)
    Number of lines in the terminal.

  columns (``<int>``)
    Number of columns in the terminal.

:source:

  `Online forum <http://www.codingtiger.com/questions/linux/
  How-to-get-console-window-width-in-python.html>`_
    '''

    import os, struct
    def ioctl_GWINSZ(fd):
      import fcntl, termios
      return struct.unpack("hh", fcntl.ioctl(fd, termios.TIOCGWINSZ, "1234"))
    # try stdin, stdout, stderr
    for fd in (0, 1, 2):
      try:
        return ioctl_GWINSZ(fd)
      except:
        pass
    # try os.ctermid()
    try:
      fd = os.open(os.ctermid(), os.O_RDONLY)
      try:
        return ioctl_GWINSZ(fd)
      finally:
        os.close(fd)
    except:
      pass
    # try `stty size`
    try:
      return tuple(int(x) for x in os.popen("stty size", "r").read().split())
    except:
      pass
    # try environment variables
    try:
      return tuple(int(os.getenv(var)) for var in ("LINES", "COLUMNS"))
    except:
      pass
    # i give up. return default.
    return (25, 80)

  # ----------------------------------------------------------------------------
  # calculate column width based on the contest (and window size)
  # ----------------------------------------------------------------------------

  @staticmethod
  def column_width(rows,columns,ifs,fit_screen=True):
    r'''
Calculate the column width based on the contents and the window size.

:arguments:

  **rows** (``<list>``)
    The rows with data. This data is referenced to as ``<dict>``. Usually the
    data is of the ``<gpbs.Job>``, ``<gpbs.Node>``, or ``<gpbs.Owner>``-class.

  **columns** (``(<dict>,<dict>,...)``)
    List with print settings. Each column has the print settings in a dictionary
    with the following fields:

    * ``'key'`` : name of the field,
    * ``'wmin'``: minimum width (otherwise exclude),
    * ``'rel'`` : relative importance of the column,

    This function creates the ``'width'``.

  **ifs** (``<str>``)
    Separator used to separate the column.

:options:

  **fit_screen** ([``True``] | ``False``)
    If set to ``True`` the column width (and the number of columns) is modified
    such that the output fits the screen.

:returns:

  **columns** (``(<dict>,<dict>,...)``)
    List with print settings. The ``'width'`` is added.
    '''

    # calculate field size
    # --------------------

    # list columns to include
    include = []

    # calculate the (maximum) width of the header and the body for each column
    for icol,column in enumerate(columns):
      # header
      column['whead'] = len(column['head'])
      # body (the rows with data)
      wmax = 0
      emax = 0
      for row in rows:
        wmax = max(wmax,len(row[column['key']]        ))
        emax = max(emax,len(row[column['key']].strip()))
      # set column with as maximum of the header/body
      column['wmax' ] = max(wmax,column['whead'])
      column['width'] = max(wmax,column['whead'])
      # check if information is present
      if emax:
        include.append(icol)

    # remove empty columns
    columns = [column for col,column in enumerate(columns) if col in include]

    # return if nothing has to be done
    if not fit_screen:
      return columns

    # check if all columns can be included
    # ------------------------------------

    # get the width needed to print all columns
    wtot = sum([column['width'] for column in columns])+(len(columns)-1)*len(ifs)
    # get the width of the current window
    wwin = Print.getTerminalSize()[1]
    # if no truncation is needed: skip truncation (equiv. to long output)
    if ( wtot<wwin ):
      return columns

    # remove columns if needed
    # ------------------------

    # set selection list, based on importance of the column
    cols = {column['rel']:i for i,column in enumerate(columns)}
    cols = [cols[i] for i in sorted(cols)]

    # leave room for truncation
    wmax = wwin
    # continue adding columns with the minimum width until the screen is filled
    wtot    = 0
    include = []
    for col in cols:
      if ( columns[col]['wmin'] < (wmax-wtot-len(ifs)) ):
        columns[col]['width'] = columns[col]['wmin']
        include.append(col)
        wtot += columns[col]['width']+len(ifs)

    # delete fields that are no longer included, and update the list of fields
    # in order of importance
    if len(include)!=len(cols):
      columns = [column for col,column in enumerate(columns) if col in include]

    # extend each of the columns as far as needed, maximum to the screen width
    # ------------------------------------------------------------------------

    # set selection list, based on importance of the column
    cols = {column['rel']:i for i,column in enumerate(columns)}
    cols = [cols[i] for i in sorted(cols)]

    # extend to columns to fill the view
    for col in cols:
      # check the total length
      wtot = sum([column['width'] for column in columns])+(len(columns)-1)*len(ifs)
      if wtot>=wwin:
        break
      # extend the column
      columns[col]['width'] = min(columns[col]['wmax'],(columns[col]['width']+wwin-wtot))

    # return final column selection
    return columns

  # ----------------------------------------------------------------------------
  # ``myqstat -f ...``
  # ----------------------------------------------------------------------------

  @staticmethod
  def myqstat_f(*args):
    r'''
Print the output of the ``qstat -f JOBID`` command.

:arguments:

  **jobid** (``<str>``)
    The job-identifiers to print.
    '''

    import commands

    (stat,qstat) = commands.getstatusoutput('/opt/torque/bin/qstat -f '+' '.join(args))

    return qstat

  # ----------------------------------------------------------------------------
  # myqstat
  # ----------------------------------------------------------------------------

  @staticmethod
  def myqstat(jobs=None,**kwargs):
    '''
Print the output for the ``qstat -f`` command.

:argument:

  **jobs** ([``None``] | ``<list>``)
    Input list of jobs.

:options:

  **owner**         ([``None`` ] | ``[<str>,...]``) Limit to owner(s)
  **exclude_owner** ([``None`` ] | ``[<str>,...]``) Exclude owner(s)
  **name**          ([``None`` ] | ``[<str>,...]``) Limit to name(s)
  **id**            ([``None`` ] | ``[<str>,...]``) Limit to id(s)
  **host**          ([``None`` ] | ``[<str>,...]``) Limit to host(s)
  **memused**       ([``None`` ] | ``[<str>,...]``) Limit to memory(ies)
  **walltime**      ([``None`` ] | ``[<str>,...]``) Limit to walltime(s)
  **sort**          ([``None`` ] | ``<str>``      ) Sort by column(s)
  **columns**       ([``None`` ] | ``<str>``      ) Set column(s)
  **add_col**       ([``None`` ] | ``<str>``      ) Add column(s) to default
  **del_col**       ([``None`` ] | ``<str>``      ) Delete column(s) from default
  **ifs**           ([``'  '`` ] | ``<str>``      ) Column separator
  **trunc**         ([``'...'``] | ``<str>``      ) Truncation symbol
  **order**         ([``'d'``  ] | ``'a'``        ) Sort order
  **nocolor**       ([``False``] | ``True``       ) No color print
  **noheader**      ([``False``] | ``True``       ) No header
  **long**          ([``False``] | ``True``       ) No truncation
    '''

    # set default options
    kwargs.setdefault('owner'        ,None )
    kwargs.setdefault('exclude_owner',None )
    kwargs.setdefault('name'         ,None )
    kwargs.setdefault('id'           ,None )
    kwargs.setdefault('host'         ,None )
    kwargs.setdefault('memused'      ,None )
    kwargs.setdefault('walltime'     ,None )
    kwargs.setdefault('sort'         ,None )
    kwargs.setdefault('columns'      ,None )
    kwargs.setdefault('add_col'      ,None )
    kwargs.setdefault('del_col'      ,None )
    kwargs.setdefault('ifs'          ,'  ' )
    kwargs.setdefault('trunc'        ,'...')
    kwargs.setdefault('order'        ,'d'  )
    kwargs.setdefault('nocolor'      ,False)
    kwargs.setdefault('noheader'     ,False)
    kwargs.setdefault('long'         ,False)

    # define column settings, based on alias [options: -s/-c]
    columns      = {}
    columns['i'] = dict(key='id'         ,head='ID'      ,wmin= 6,rel= 0)
    columns['o'] = dict(key='owner'      ,head='Owner'   ,wmin= 7,rel= 2)
    columns['n'] = dict(key='name'       ,head='Job name',wmin=11,rel= 9)
    columns['h'] = dict(key='host'       ,head='Host'    ,wmin= 2,rel= 3)
    columns['c'] = dict(key='resnode'    ,head='CPUs'    ,wmin= 6,rel= 5)
    columns['p'] = dict(key='pmem'       ,head='pmem'    ,wmin= 5,rel= 8)
    columns['m'] = dict(key='memused'    ,head='Mem'     ,wmin= 5,rel= 4)
    columns['s'] = dict(key='state'      ,head='S'       ,wmin= 1,rel= 1)
    columns['t'] = dict(key='walltime'   ,head='Time'    ,wmin= 4,rel= 6)
    columns['r'] = dict(key='score'      ,head='Score'   ,wmin= 4,rel= 7)
    columns['a'] = dict(key='submit_args',head='qsub'    ,wmin=11,rel=10)
    # get column name based on alias
    alias = {columns[a]['key']:a for a in columns}

    # read jobs
    if jobs is None:
      jobs = Read.myqstat()

    # if filter applied: limit list of jobs to filter
    for name in ['owner','name','id','walltime','host','memused']:
      if kwargs[name] is not None:
        # - set color
        columns[alias[name]]['color'] = 'selection'
        # - apply filter
        if name in ['owner','name','id']: jobs = [[job for job in jobs if re.match(item,         job[columns[alias[name]]['key']])] for item in kwargs[name]]
        else                            : jobs = [[job for job in jobs if          item==getattr(job,columns[alias[name]]['key']) ] for item in kwargs[name]]
        # - select jobs
        jobs = [ job for sub in jobs for job in sub]

    # if filter applied: exclude from list of jobs
    for key in ['exclude_owner']:
      name = key.split('exclude_')[1]
      if kwargs[key] is not None:
        # - set color
        columns[alias[name]]['color'] = 'selection'
        # - initiate to include or not
        incl = [False for i in jobs]
        # - loop over jobs
        for (ijob,job) in enumerate(jobs):
          if name in ['owner','name','id']: incl[ijob] = len([i for i in kwargs[key] if re.match(i,         job[columns[alias[name]]['key']])])==0
          else                            : incl[ijob] = len([i for i in kwargs[key] if          i==getattr(job,columns[alias[name]]['key']) ])==0
        # - select jobs
        jobs = [job for job,i in zip(jobs,incl) if i]

    # apply sort to the list of jobs
    if kwargs['sort']:
      for s in kwargs['sort']:
        jobs = sorted(jobs,key=lambda job: getattr(job,columns[s]['key']))

    # convert the order of jobs
    if kwargs['order']!='a':
      jobs = [job for job in jobs[-1::-1]]

    # set default column list
    col = ['i','o','n','h','c','m','p','s','t','r']
    # add/remove/overwrite column list
    if kwargs['add_col']:
      col += [c for c in kwargs['add_col']]
    if kwargs['del_col']:
      rm   = [c for c in kwargs['del_col']]
      col  = [c for c in col if c not in rm]
    if kwargs['columns']:
      col  = [c for c in kwargs['columns']]

    # select columns -> convert to list
    columns = [columns[c] for c in col]

    # calculate column width
    columns = Print.column_width(jobs,columns,ifs=kwargs['ifs'],fit_screen=not kwargs['long'])

    # set the colors
    if kwargs['nocolor']: color = ColorNone
    else                : color = ColorDefault

    # print output
    if len(jobs)>0:
      if not kwargs['noheader']:
        print jobs[0].print_header(columns,line='=',ifs=kwargs['ifs'],trunc=kwargs['trunc']).format(color=color)
      for job in jobs:
        print job.print_column(columns,ifs=kwargs['ifs'],trunc=kwargs['trunc']).format(color=color)

  # ----------------------------------------------------------------------------
  # myqstat_node
  # ----------------------------------------------------------------------------

  @staticmethod
  def myqstat_node(nodes=None,**kwargs):
    '''
Print the output for the ``pbsnodes`` (and ``ganglia``) command(s).

:argument:

  **nodes** ([``None``] | ``<list>``)
    Input list of nodes.

:options:

  **sort**          ([``None`` ] | ``<str>``) Sort by column(s)
  **columns**       ([``None`` ] | ``<str>``) Set column(s)
  **add_col**       ([``None`` ] | ``<str>``) Add column(s) to default
  **del_col**       ([``None`` ] | ``<str>``) Delete column(s) from default
  **ifs**           ([``'  '`` ] | ``<str>``) Column separator
  **trunc**         ([``'...'``] | ``<str>``) Truncation symbol
  **order**         ([``'d'``  ] | ``'a'``  ) Sort order
  **nocolor**       ([``False``] | ``True`` ) No color print
  **noheader**      ([``False``] | ``True`` ) No header
  **long**          ([``False``] | ``True`` ) No truncation / ganglia
    '''

    # set default options
    kwargs.setdefault('sort'    ,None )
    kwargs.setdefault('columns' ,None )
    kwargs.setdefault('add_col' ,None )
    kwargs.setdefault('del_col' ,None )
    kwargs.setdefault('ifs'     ,'  ' )
    kwargs.setdefault('trunc'   ,'...')
    kwargs.setdefault('order'   ,'d'  )
    kwargs.setdefault('nocolor' ,False)
    kwargs.setdefault('noheader',False)
    kwargs.setdefault('long'    ,False)

    # define column settings, based on alias [options: -s/-c]
    columns      = {}
    columns['n'] = dict(key='node'      ,head='Node'   ,wmin=4,rel= 0)
    columns['s'] = dict(key='state'     ,head='State'  ,wmin=6,rel= 1)
    columns['t'] = dict(key='ctype'     ,head='Type'   ,wmin=5,rel= 2)
    columns['c'] = dict(key='ncpu'      ,head='Ctot'   ,wmin=4,rel= 3)
    columns['f'] = dict(key='cpufree'   ,head='Cfree'  ,wmin=5,rel= 4)
    columns['m'] = dict(key='memp'      ,head='Mtot'   ,wmin=5,rel= 5)
    columns['w'] = dict(key='memu'      ,head='Mused'  ,wmin=6,rel= 6)
    columns['p'] = dict(key='relmemu'   ,head='Mem%'   ,wmin=5,rel= 7)
    columns['r'] = dict(key='score'     ,head='Score'  ,wmin=4,rel= 8)
    columns['h'] = dict(key='disk_total',head='HDtot'  ,wmin=6,rel= 9)
    columns['e'] = dict(key='disk_used' ,head='HDused' ,wmin=6,rel=10)
    columns['x'] = dict(key='reldisku'  ,head='HD%'    ,wmin=5,rel=11)
    columns['b'] = dict(key='bytes_tot' ,head='Network',wmin=7,rel=12)

    # read host information
    if nodes is None:
      nodes = Read.myqstat_node(kwargs['long'])

    # apply sort to the (remaining) list of nodes
    if kwargs['sort'] is None:
      kwargs['sort'] = ['n']
    for s in kwargs['sort']:
      nodes = sorted(nodes,key=lambda node: getattr(node,columns[s]['key']))

    # convert the order of nodes
    if kwargs['order']!='a':
      nodes = [node for node in nodes[-1::-1]]

    # set default column list
    col = ['n','s','t','c','f','r','m','p']
    if kwargs['long']:
      col += ['h','x','b']
    # add/remove/overwrite column list
    if kwargs['add_col']:
      col += [c for c in kwargs['add_col']]
    if kwargs['del_col']:
      rm   = [c for c in kwargs['del_col']]
      col  = [c for c in col if c not in rm]
    if kwargs['columns']:
      col  = [c for c in kwargs['columns']]

    # select columns -> convert to list
    columns = [columns[c] for c in col]

    # calculate column width
    columns = Print.column_width(nodes,columns,ifs=kwargs['ifs'],fit_screen=not kwargs['long'])

    # set the colors
    if kwargs['nocolor']: color = ColorNone
    else                : color = ColorDefault

    # print output
    if len(nodes)>0:
      if not kwargs['noheader']:
        print nodes[0].print_header(columns,line='=',ifs=kwargs['ifs'],trunc=kwargs['trunc']).format(color=color)
      for job in nodes:
        print job.print_column(columns,ifs=kwargs['ifs'],trunc=kwargs['trunc']).format(color=color)

    # summary
    # -------

    # total number of CPUs
    total   = [str(sum([node.ncpu for node in nodes]))]
    fmt     = '%'+str(len(total[0]))+'d'
    cfmt    = fmt+' %s'
    # list CPU-types
    ctypes  = list(set([node.ctype for node in nodes]))
    # offline/online/working/free CPUs
    offline = [fmt%sum([node.ncpu              for node in nodes if node.state not in ['free','job-exclusive']])]
    online  = [fmt%sum([node.ncpu              for node in nodes if node.state     in ['free','job-exclusive']])]
    working = [fmt%sum([node.ncpu-node.cpufree for node in nodes if node.state     in ['free','job-exclusive']])]
    free    = [fmt%sum([node.cpufree           for node in nodes if node.state     in ['free','job-exclusive']])]

    # if more than one CPU-type is present: differentiate between CPU-types
    if len(ctypes)>1:
      for ctype in ctypes:
        total   += [cfmt%(sum([node.ncpu              for node in nodes if node.ctype==ctype                                               ]),ctype)]
        offline += [cfmt%(sum([node.ncpu              for node in nodes if node.ctype==ctype and node.state not in ['free','job-exclusive']]),ctype)]
        online  += [cfmt%(sum([node.ncpu              for node in nodes if node.ctype==ctype and node.state     in ['free','job-exclusive']]),ctype)]
        working += [cfmt%(sum([node.ncpu-node.cpufree for node in nodes if node.ctype==ctype and node.state     in ['free','job-exclusive']]),ctype)]
        free    += [cfmt%(sum([node.cpufree           for node in nodes if node.ctype==ctype and node.state     in ['free','job-exclusive']]),ctype)]

    # convert to text
    total   = 'number of CPUs total    : '+total  [0]+(' ( '+' / '.join(total  [1:])+' )' if len(total  )>1 else '')
    offline = 'number of CPUs offline  : '+offline[0]+(' ( '+' / '.join(offline[1:])+' )' if len(offline)>1 else '')
    online  = 'number of CPUs online   : '+online [0]+(' ( '+' / '.join(online [1:])+' )' if len(online )>1 else '')
    working = 'number of CPUs working  : '+working[0]+(' ( '+' / '.join(working[1:])+' )' if len(working)>1 else '')
    free    = 'number of CPUs free     : '+free   [0]+(' ( '+' / '.join(free   [1:])+' )' if len(free   )>1 else '')

    # print
    print '-'*len(total)
    print total
    print offline
    print online
    print working
    print free

  # ----------------------------------------------------------------------------
  # myqstat_user
  # ----------------------------------------------------------------------------

  @staticmethod
  def myqstat_user(owners=None,**kwargs):
    '''
Print the output for the ``myqstat -U`` command.

:argument:

  **owners** ([``None``] | ``<list>``)
    Input list of owners.

:options:

  **sort**          ([``None`` ] | ``<str>``) Sort by column(s)
  **columns**       ([``None`` ] | ``<str>``) Set column(s)
  **add_col**       ([``None`` ] | ``<str>``) Add column(s) to default
  **del_col**       ([``None`` ] | ``<str>``) Delete column(s) from default
  **ifs**           ([``'  '`` ] | ``<str>``) Column separator
  **trunc**         ([``'...'``] | ``<str>``) Truncation symbol
  **order**         ([``'d'``  ] | ``'a'``  ) Sort order
  **nocolor**       ([``False``] | ``True`` ) No color print
  **noheader**      ([``False``] | ``True`` ) No header
  **long**          ([``False``] | ``True`` ) No truncation
    '''

    # set default options
    kwargs.setdefault('sort'    ,None )
    kwargs.setdefault('columns' ,None )
    kwargs.setdefault('add_col' ,None )
    kwargs.setdefault('del_col' ,None )
    kwargs.setdefault('ifs'     ,'  ' )
    kwargs.setdefault('trunc'   ,'...')
    kwargs.setdefault('order'   ,'d'  )
    kwargs.setdefault('nocolor' ,False)
    kwargs.setdefault('noheader',False)
    kwargs.setdefault('long'    ,False)

    # define column settings, based on alias [options: -s/-c]
    columns      = {}
    columns['o'] = dict(key='owner'      ,head='Owner',wmin= 7,rel= 0)
    columns['c'] = dict(key='cpus'       ,head='CPUs' ,wmin= 3,rel= 1)
    columns['m'] = dict(key='memused'    ,head='Mem'  ,wmin= 5,rel= 2)
    columns['t'] = dict(key='walltime'   ,head='Time' ,wmin= 5,rel= 3)
    columns['r'] = dict(key='score'      ,head='Score',wmin= 4,rel= 7)

    # read node information
    if owners is None:
      owners = Read.myqstat_user()

    # apply sort to the (remaining) list of nodes
    if kwargs['sort'] is None:
      kwargs['sort'] = ['c']
    for s in kwargs['sort']:
      owners = sorted(owners,key=lambda owner: getattr(owner,columns[s]['key']))

    # convert the order of owner
    if kwargs['order']!='a':
      owners = [owner for owner in owners[-1::-1]]

    # set default column list
    col = ['o','c','m','t','r']
    # add/remove/overwrite column list
    if kwargs['add_col']:
      col += [c for c in kwargs['add_col']]
    if kwargs['del_col']:
      rm   = [c for c in kwargs['del_col']]
      col  = [c for c in col if c not in rm]
    if kwargs['columns']:
      col  = [c for c in kwargs['columns']]

    # select columns -> convert to list
    columns = [columns[c] for c in col]

    # calculate column width
    columns = Print.column_width(owners,columns,ifs=kwargs['ifs'],fit_screen=not kwargs['long'])

    # set the colors
    if kwargs['nocolor']: color = ColorNone
    else                : color = ColorDefault

    # print output
    if len(owners)>0:
      if not kwargs['noheader']:
        print owners[0].print_header(columns,line='=',ifs=kwargs['ifs'],trunc=kwargs['trunc']).format(color=color)
      for owner in owners:
        print owner.print_column(columns,ifs=kwargs['ifs'],trunc=kwargs['trunc']).format(color=color)





# ##############################################################################
# -------------------------- PART 3 - CREATE SCRIPTS --------------------------
# ##############################################################################

class script:
  '''
Return common PBS-scripts as string. The following scripts are implemented:

* ``simple``: a basic PBS-script that executes (a series of) command(s).

* ``heavyio``: uses a temporary working directory on the compute-node.
  '''

  tempdir = '/state/partition1/{user:s}/{jobid:s}'

  # ----------------------------------------------------------------------------

  @staticmethod
  def simple(pbsopt=[],command=None):
    '''
Simple PBS-script.

:options:

  **pbsopt** (``<list>``)
    List with PBS options.

  **command** (``<str>``)
    Commands to execute.
    '''

    import re

    pbsopt = [pbsopt] if type(pbsopt)==str else pbsopt
    pbsdef = []

    # set default options
    defaults = (
      ('-S .*'     ,'-S /bin/bash'    ),
      ('-j .*'     ,'-j oe'           ),
      ('-o .*'     ,'-o pbs.out'      ),
      ('-l nodes.*','-l nodes=1:ppn=1'),
    )
    for check,default in defaults:
      if len([opt for opt in pbsopt if re.match(check,opt)])==0:
        pbsdef.append(default)
    pbsopt = pbsdef+pbsopt

    # create script
    return '\n'.join([
      '#!/bin/bash',
      '#PBS '+'\n#PBS '.join(pbsopt),
      '''
# change current directory, to location of qsub command
cd ${PBS_O_WORKDIR}

      ''',
      'echo "Commands go here"' if command is None else command])

  # ----------------------------------------------------------------------------

  @staticmethod
  def heavyio(pbsopt=[],command=None):
    '''
Create a heavy-io PBS-script to use a temporary working directory on the
compute-node.

:options:

  **pbsopt** (``<list>``)
    List with PBS options.

  **command** (``<str>``)
    Commands to execute.
    '''

    import re

    pbsopt = [pbsopt] if type(pbsopt)==str else pbsopt
    pbsdef = []

    # set default options
    defaults = (
      ('-S .*'     ,'-S /bin/bash'    ),
      ('-j .*'     ,'-j oe'           ),
      ('-o .*'     ,'-o pbs.out'      ),
      ('-l nodes.*','-l nodes=1:ppn=1'),
    )
    for check,default in defaults:
      if len([opt for opt in pbsopt if re.match(check,opt)])==0:
        pbsdef.append(default)
    pbsopt = pbsdef+pbsopt

    # create script
    return '\n'.join([
      '#!/bin/bash',
      '#PBS '+'\n#PBS '.join(pbsopt),
      '''
# store my username
username=`whoami`

# set the name of the temporary directory on the compute-node
# the name is a combination of the username and the job-id
# assigned by the queuing system
computedir="/state/partition1/$username/${PBS_JOBID%%.*}"

# 1. Transfer to node
# ===================

# create temp directory
if [ ! -d "$computedir" ]; then
   # if it does not exist, create
   mkdir -p "$computedir"
else
   # else, empty the directory
   rm -rf "${computedir}"/*
fi

# change current directory, to location of qsub command
# typically in the home directory on the head-node
cd ${PBS_O_WORKDIR}
# copy input files
cp -prf * $computedir
# change directory to the temporary directory on the compute-node
cd $computedir

# 2. Execute
# ==========
      ''',
      'echo "Commands go here"' if command is None else command,
      '''
# 3. Transfer back to the head-node
# =================================

# change to directory to the home directory (on the head-node)
cd "${PBS_O_WORKDIR}"
# copy everything from the compute-node
cp -prf "${computedir}"/* .
# erase the temp directory on compute-node
rm -rf "$computedir"

      '''])





# ==============================================================================

if __name__=='__main__':
  pass
