:tocdepth: 2

.. _gpbs:

****************
Custom PBS tools
****************

.. contents:: **Outline**
  :local:
  :depth: 1
  :backlinks: top

``gpbs`` - PBS-status module for Python
=======================================

.. contents::
  :local:
  :depth: 1
  :backlinks: top

Main interface
--------------

The main interaction with the ``gpbs`` module is with the following functions.

.. autosummary::

    gpbs.myqstat
    gpbs.myqstat_node
    gpbs.myqstat_user

These function respectively output lists of the ``<gpbs.Job>``, ``<gpbs.Node>``,
or ``<gpbs.Owner>`` class. Each item has fields that are strings, integers, but
also some custom classes discussed below.

.. autosummary::

    gpbs.Job
    gpbs.Node
    gpbs.Owner

Formatted print
---------------

The ``<gpbs.Job>``, ``<gpbs.Node>``, and ``<gpbs.Owner>`` classes have three
methods to print information, as follows

.. contents::
  :local:
  :depth: 1
  :backlinks: top

Default string
""""""""""""""

To obtain a field as string without caring too much about the formatting, the
class-item can be referenced to as a dictionary. For example:

.. code-block:: python

  # read list of jobs
  jobs = gpbs.myqstat()

  # print the 'walltime' field of each job, with default formatting
  for job in jobs:
    print job['walltime']

This can be used for basic print operations, or to read the length of the
string.

Formatted print
"""""""""""""""

To keep full control, all of the classes are constructed such that they respond
to the ``format`` command. Most of the formatting rules coincide with the
default Python rules. However the ``<gpbs.Host>`` and ``<gpbs.ResNode>`` have
some custom features. For the general interaction consider the following
example:

.. code-block:: python

  # read list of jobs
  jobs = gpbs.myqstat()

  # print rows with information per job
  for job in jobs:
    print '{job.id:>6.6s}, {job.host:>3s}, {job.pmem:>5s}'.format(job=job)

Column print
""""""""""""

To print the information as columns, consider the following example:

.. code-block:: python

  # define column settings
  columns = [
    dict(key='id'   ,head='id'   ,width=6),
    dict(key='score',head='score',width=4),
  ]

  # read list of jobs
  jobs = gpbs.myqstat()

  # print headers of the columns
  print jobs[0].print_header(columns)

  # print jobs in columns
  for job in jobs:
    print job.print_column(columns).format(color=gpbs.ColorDefault)

Custom classes
--------------

Several fields of the ``<gpbs.Job>``, ``<gpbs.Node>``, and ``<gpbs.Owner>``
classes are stored as a custom class. These classes provide methods to convert
strings to data, and reconvert the data to a humanly readable string. The
following classes are used.

.. autosummary::

    gpbs.Host
    gpbs.ResNode
    gpbs.Time
    gpbs.Data
    gpbs.Float

Module details
--------------

To understand the details of the module, it is important to be aware that
several classes (and functions) are derived from a parent class. The following
parents with children are distinguished.

Store information
"""""""""""""""""

.. autosummary::

    gpbs.Item
    gpbs.Job
    gpbs.Node
    gpbs.Owner

Store data
""""""""""

.. autosummary::

    gpbs.Host
    gpbs.ResNode

Store with unit and/or ``None``
"""""""""""""""""""""""""""""""

.. autosummary::

    gpbs.Unit
    gpbs.Time
    gpbs.Data
    gpbs.Float

Read output
"""""""""""

.. autosummary::

    gpbs.read_qstat
    gpbs.read_pbs
    gpbs.myqstat
    gpbs.myqstat_node
    gpbs.myqstat_user

Module details
""""""""""""""

.. automodule:: gpbs
   :members:

``myqstat`` - show status of jobs and nodes
===========================================

Installation
------------

1.  Store the file ``myqstat`` somewhere, and make sure that it is executable.
    For example:

    .. code-block:: bash

      [user@pc     ] $ scp myqstat user@furnace:~/bin/
      [user@pc     ] $ ssh user@furnace
      [user@furnace] $ cd ~/bin
      [user@furnace] $ chmod u+x myqstat

2.  Make sure that the folder in which ``myqstat`` is in the ``PATH`` in which
    Bash looks for executables. Following the above example:

    .. code-block:: bash

      [user@furnace] $ export PATH=$HOME/bin:$PATH

    To avoid having to do this more than once, add this line to the
    ``~/.bashrc`` file, which is executed upon login.

3.  Store the ``gpbs.py`` module in the same folder as ``myqstat``, or otherwise
    make sure that Python can find it in the ``PYTHONPATH``. For example:

    .. code-block:: bash

      [user@furnace] $ export PYTHONPATH=$HOME/bin:$PYTHONPATH

    To avoid having to do this more than once, add this line to the
    ``~/.bashrc`` file, which is executed upon login.

The command can now be used. Try:

.. code-block:: bash

  [user@furnace] $ myqstat

To get more information on the options:

.. code-block:: bash

  [user@furnace] $ myqstat -h
  [user@furnace] $ myqstat --help

Implementation details
----------------------

By calling ``Main()`` the command-line argument parser is invoked. This parser
deals with all the input options, and at the end of the ``__init__()`` function
calls one of the following functions, before exiting:

* ``help``        : acts on ``myqstat -h``
* ``version``     : acts on ``myqstat -v``
* ``myqstat``     : acts on ``myqstat``
* ``myqstat_node``: acts on ``myqstat -N``
* ``myqstat_user``: acts on ``myqstat -U``

The latter three functions use the ``gpbs`` module to read, convert, and print
the data of the relevant commands. The local ``getTerminalSize`` and
``column_width`` functions are used to adapt the output to the size available
in the current window.

