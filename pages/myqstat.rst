:tocdepth: 2

.. _monitoring:

**************************
Job monitoring and control
**************************

.. topic:: Use default versions on MaTe-clusters

  All scripts below are available on the MaTe-clusters in the ``/share/apps/extra/bin``-folder. They can be readily used by including the following line in the ``~/.bashrc``:

  .. code-block:: bash

    export PATH=/share/apps/extra/bin:$PATH

  **NB** this includes selecting the (newer) Python installation in ``/share/apps/extra``` over the default Python-executable

.. topic:: "Installation" for custom use

  Downloads:

  * :download:`gpbs.py <../myqstat/gpbs.py>`
  * :download:`myqstat <../myqstat/myqstat>`
  * :download:`qdelall <../myqstat/qdelall>`
  * :download:`qexec <../myqstat/qexec>`
  * :download:`qfilter <../myqstat/qfilter>`
  * :download:`qcp <../myqstat/qcp>`

  All of the shell-scripts below are written in Python, but can be used as any shell-script. However, they all depend on the (custom) ``gpbs``-module. This module must be made available before the scripts can be used. The steps below "install" ``myqstat``, the same steps hold for the other scripts.

  1.  Store the file ``myqstat`` somewhere, and make sure that it is executable. For example:

      .. code-block:: bash

        [user@pc     ] $ scp myqstat user@furnace:~/bin/
        [user@pc     ] $ ssh user@furnace
        [user@furnace] $ cd ~/bin
        [user@furnace] $ chmod u+x myqstat

  2.  Make sure that the folder in which ``myqstat`` is in the ``PATH`` in which Bash looks for executables. Following the above example:

      .. code-block:: bash

        [user@furnace] $ export PATH=$HOME/bin:$PATH

      To avoid having to do this more than once, add this line to the ``~/.bashrc`` file, which is executed upon login.

  3.  Store the ``gpbs.py`` module in the same folder as ``myqstat``, or otherwise make sure that Python can find it in the ``PYTHONPATH``. For example:

      .. code-block:: bash

        [user@furnace] $ export PYTHONPATH=$HOME/bin:$PYTHONPATH

      To avoid having to do this more than once, add this line to the ``~/.bashrc`` file, which is executed upon login.

  The command can now be used. Try:

  .. code-block:: bash

    [user@furnace] $ myqstat --help

  or

  .. code-block:: bash

    [user@furnace] $ myqstat

.. _monitoring_myqstat:

``myqstat``
===========

The ``myqstat``-command prints prints the output of the ``qstat -f``, ``pbsnodes`` and/or ``ganglia`` command in an easy to understand output.

For example:

.. code-block:: none

  $ myqstat

  ID   Owner    Job name  Host  CPUs  Mem  S  Time  Score
  ===  =======  ========  ====  ====  ===  =  ====  =====
  690  tdegeus  job.pbs     17   1:1  1gb  R  7.2m   0.99

  $ myqstat -U

  owner     cpus  mem    time  score
  ========  ====  =====  ====  =====
  tdegeus      1    1gb    7m   0.99

  $ myqstat -N

  Node  State          Ctot  Cfree  Score  Mtot   Mem%
  ====  =============  ====  =====  =====  =====  ====
     0  free             16     16   1.00  265gb  0.01
     1  free             16     15   0.99  265gb  0.01
  -----------------------------
  number of CPUs total    :  32
  number of CPUs offline  :   0
  number of CPUs online   :  32
  number of CPUs working  :   1
  number of CPUs free     :  31

Popular options include:

* ``myqstat -u``: limit output to that belonging to the current user
* ``myqstat -u NAME``: limit output to specific user
* ``myqstat -w``: limit output to all other users except the current user
* ``myqstat -w NAME``: limit output to all other users except the specified user
* ``myqstat -U``: print a summary per user
* ``myqstat -N``: print a summary per node

``qdelall``
===========

The ``qdelall``-command can delete a group of jobs using simple filters. For example:

.. code-block:: bash

  # delete all of the user's jobs
  $ qdelall

  # delete all of the user's jobs,
  # but ask for confirmation before deleting the jobs
  $ qdelall -v

  # delete all of the user's jobs and try to remove the temporary directory
  # on the compute-node
  $ qdelall -t

``qexec``
=========

The ``qexec``-command can submit a group of jobs using a single commands. It can also be used to submit a very large batch of jobs, whereby only a prespecified number of jobs is run in parallel. For example:


.. code-block:: bash

  $ qexec -i sim*/*.pbs

To remove the running jobs from the input list of (PBS-)files use the ``qfilter``-command.

``qcp``
=======

The ``qcp``-command copies data from a temporary working directory on the compute-node to the job's directory on the head-node.

.. _implemenation:

**********************
Implementation details
**********************

``myqstat``
===========

By calling ``Main()`` the command-line argument parser is invoked. This parser
deals with all the input options, and at the end of the ``__init__()`` function
calls one of the following functions, before exiting:

* ``help``        : acts on ``myqstat -h``
* ``version``     : acts on ``myqstat -v``
* ``myqstat``     : acts on ``myqstat``
* ``myqstat_node``: acts on ``myqstat -N``
* ``myqstat_user``: acts on ``myqstat -U``

The latter three functions use the ``gpbs``-module to read, convert, and print
the data of the relevant commands. The local ``getTerminalSize`` and
``column_width`` functions are used to adapt the output to the size available
in the current window.

``gpbs.py``
===========

.. contents:: **Outline**
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

All these classes have the customized functionality to obtain a field as data or
as string (with a certain formatting default). Consider the following example:

.. code-block:: python

  >>> type(job.cputime)
  <class 'gpbs.Time'>

  >>> type(job['cputime'])
  <str>

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


