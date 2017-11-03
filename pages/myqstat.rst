:tocdepth: 2

.. _monitoring:

**************************
Job monitoring and control
**************************

.. contents:: Contents
    :local:
    :depth: 2
    :backlinks: top

Advanced job submit
===================

Submit a batch job
------------------

Consider the following example:

* Each job is a sub-directory of the current path, in this example ``sim0``, ``sim1``, and ``sim2``.

* Each job has a file ``job.pbs`` to control the job.

To submit all the jobs:

.. code-block:: bash

  # store the current directory
  froot=$(pwd);
  # loop over all files "job.pbs"
  for name in `find . -iname 'job.pbs'`;
  do
    # separate the name of the PBS-file "p" and the directory "f"
    f=`echo $name | rev | cut -d"/" f2- | rev`
    p=`echo $name | rev | cut -d"/" f1  | rev`
    # go the the proper directory, submit, and go back to current directory
    cd $f;
    qsub -N $f job.pbs;
    cd $froot;
  done

* The Bash ``for``-loop is used to loop over space separated list of names:

  .. code-block:: bash

    for name in "sim0" "sim1" "sim2";
    do
      echo $name;
    done

  would display:

  .. code-block:: bash

    sim0
    sim1
    sim2

* The list of jobs to submit is generate using the :command:`find`-command:

  .. code-block:: bash

    find . -iname 'job.pbs'

  lists

  .. code-block:: bash

    sim0/job.pbs
    sim1/job.pbs
    sim2/job.pbs

* The :command:`cut`-command is used to split the output of the :command:`find`-command in the name of the directory

  .. code-block:: bash

    echo $name | rev | cut -d"/" f2- | rev

  by reversing the string, including everything from the first ``/`` onward, and reversing the resulting string to it's original order. This corresponds to including everything up to the last ``/``. In the same way the name of the PBS-file is extracted from the output of the :command:`find`-command.

* The :command:`cd`-command is used to proceed to the simulation sub-directory, after which the simulation is submitted. Then :command:`cd` is used again to go back to the original directory.

.. note::

  The :command:`qexec`-command can do this automatically:

  .. code-block:: bash

    qexec -i `find . -iname 'job.pbs'`

  This command has much more options. See: :ref:`monitoring_qexec`, and ``qexec --help``.

Submit part of a batch job
--------------------------

Consider the following example (similar to above):

* Each job is a sub-directory of the current path.

* Each job has a file ``job.pbs`` to control the job.

* A completed job has the file ``pbs.out``, a job that has not been completed yet does not contain this file.

To submit all jobs that have not yet been completed:

.. code-block:: bash

  for f in `find . -mindepth 1 -maxdepth 1 -type d -exec test ! -e '{}/pbs.out' \; -printf '%p '`;
  do
    cd $f;
    qsub job.pbs;
    cd ..;
  done

Let us study the command that lists all folders **not** containing a specific file "pbs.out":

.. code-block:: bash

  find . -mindepth 1 -type d -exec test ! -e '{}/pbs.out' \; -print

* List the directory names, using the :command:`find`-command:

  ``find .``
    find files/directories from the current directory downwards.

  ``-mindepth 1``
    limit the search to at least one directory downwards (at least a sub-directory). To list only sub-directories (and not sub-sub-directories, etc) extend with ``-maxdepth 1``.

  ``-type d``
    limit the result to directories.

  ``-exec``
    execute a command on the search result.

* List only those directories not containing the file ``pbs.out``, using the ``test``-command:

  ``test``
    check file types and compare values.

  ``!``
    list the result for which the expression is false.

  ``-e '{}/pbs.out'``
    check if the file ``pbs.out`` exists. The ``-e`` option comes from the :command:`test`-command. The ``{}`` is the way to include the search result from the :command:`find`-command (in this case the sub-directories.

* List the result:

  ``\;``
    terminates the :command:`find`-command.

  ``-print``
    print the full file name on the standard output, followed by a newline.

.. note::

  The :command:`qfilter`-command can do this automatically. In fact, it also checks if the job has already been submitted (instead of only checking if it is completed). For example together with the :command:`qexec`-command:

  .. code-block:: bash

    qexec -i `find . -iname 'job.pbs' | qfilter`

  This command has much more options. See: :ref:`monitoring_qfilter`, and ``qfilter --help``.


Custom scripts
==============

.. contents:: **Outline**
  :local:
  :depth: 3
  :backlinks: top

Downloads
---------

* :download:`gpbs.py <../myqstat/gpbs.py>`
* :download:`myqstat <../myqstat/myqstat>`
* :download:`qdelall <../myqstat/qdelall>`
* :download:`qexec <../myqstat/qexec>`
* :download:`qfilter <../myqstat/qfilter>`
* :download:`qcp <../myqstat/qcp>`

Use default versions on MaTe-clusters
-------------------------------------

All scripts below are available on the MaTe-clusters in the ``/share/apps/extra/bin``-folder. They can be readily used by including the following line in the ``~/.bashrc``:

.. code-block:: bash

  export PATH=/share/apps/extra/bin:$PATH

**NB** this includes selecting the (newer) Python installation in ``/share/apps/extra`` over the default Python-executable

"Installation" for custom use
-----------------------------

All of the shell-scripts below are written in Python, but can be used as any shell-script. However, they all depend on the (custom) :command:`gpbs`-module. This module must be made available before the scripts can be used. The steps below "install" :command:`myqstat`, the same steps hold for the other scripts.

1.  Store the file :command:`myqstat` somewhere, and make sure that it is executable. For example:

    .. code-block:: bash

      [user@pc     ] $ scp myqstat user@furnace:~/bin/
      [user@pc     ] $ ssh user@furnace
      [user@furnace] $ cd ~/bin
      [user@furnace] $ chmod u+x myqstat

2.  Make sure that the folder in which :command:`myqstat` is in the ``PATH`` in which Bash looks for executables. Following the above example:

    .. code-block:: bash

      [user@furnace] $ export PATH=$HOME/bin:$PATH

    To avoid having to do this more than once, add this line to the ``~/.bashrc`` file, which is executed upon login.

3.  Store ``gpbs.py`` in the same folder as :command:`myqstat`, or otherwise make sure that Python can find it in the ``PYTHONPATH``. For example:

    .. code-block:: bash

      [user@furnace] $ export PYTHONPATH=$HOME/bin:$PYTHONPATH

    To avoid having to do this more than once, add this line to the ``~/.bashrc`` file.

The command can now be used. Try:

.. code-block:: bash

  [user@furnace] $ myqstat --help

or

.. code-block:: bash

  [user@furnace] $ myqstat

.. _monitoring_myqstat:

myqstat
-------

The :command:`myqstat`-command prints prints the output of the ``qstat -f``, ``pbsnodes`` and/or ``ganglia`` command in an easy to understand output.

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

.. _monitoring_qdelall:

qdelall
-------

The :command:`qdelall`-command can delete a group of jobs using simple filters. For example:

.. code-block:: bash

  # delete all of the user's jobs
  $ qdelall

  # delete all of the user's jobs,
  # but ask for confirmation before deleting the jobs
  $ qdelall -v

  # delete all of the user's jobs and try to remove the temporary directory
  # on the compute-node
  $ qdelall -t

.. note::

  The robustness of the script still needs to be tested.

.. _monitoring_qexec:

qexec
-----

The :command:`qexec`-command can submit a group of jobs using a single command. It can also be used to submit a very large batch of jobs, whereby only a prespecified number of jobs is run in parallel. For example:


.. code-block:: bash

  $ qexec -i sim*/*.pbs

To remove the running jobs from the input list of (PBS-)files use the :ref:`monitoring_qfilter`-command.

.. note::

  The robustness of the script still needs to be tested.

.. _monitoring_qfilter:

qfilter
-------

The :command:`qfilter`-command can filter a list of jobs from jobs that have been completed or are running, but checking the existence of an output-file.

.. note::

  The robustness of the script still needs to be tested.

.. _monitoring_qcp:

qcp
---

The :command:`qcp`-command copies data from a temporary working directory on the compute-node to the job's directory on the head-node.

.. note::

  The robustness of the script still needs to be tested.


.. _implemenation:

**********************
Implementation details
**********************

myqstat
=======

Handles the command-line options and print the cluster's states using ``gpbs.py``.

gpbs.py
=======

.. contents:: **Outline**
  :local:
  :depth: 1
  :backlinks: top

Automatic formatted print
-------------------------

.. autosummary::

    gpbs.Print.myqstat
    gpbs.Print.myqstat_node
    gpbs.Print.myqstat_user

Read to list
------------

.. autosummary::

    gpbs.Read.myqstat
    gpbs.Read.myqstat_node
    gpbs.Read.myqstat_user

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

Customized formatted print
--------------------------

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
default Python3 rules. However the ``<gpbs.Host>`` and ``<gpbs.ResNode>`` have
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

Main interface
""""""""""""""

.. autosummary::

    gpbs.Read.myqstat
    gpbs.Read.myqstat_node
    gpbs.Read.myqstat_user
    gpbs.Print.myqstat
    gpbs.Print.myqstat_node
    gpbs.Print.myqstat_user

Module details
""""""""""""""

.. automodule:: gpbs
   :members:


