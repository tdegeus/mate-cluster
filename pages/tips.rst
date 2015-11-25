:tocdepth: 2

############
FAQ and tips
############

.. contents:: **Outline**
  :local:
  :depth: 1
  :backlinks: top


Frequently asked questions (FAQ)
================================

.. contents:: **FAQ**
    :local:
    :depth: 2
    :backlinks: top

I want to stop my job, what should I do?
----------------------------------------

1. Obtain the job-id using the ``myqstat`` (or ``qstat``) command. For example:

   .. code-block:: bash

      [username@furnace ~]$ myqstat

      jid    , owner     , jobname       , host , cpus   , mem  , S , time , score
      ------ , --------- , ------------- , ---- , ------ , ---- , — , ---- , -----
      202169 , username  , myjob.pbs     ,   11 ,  1:1:i ,  1mb , R ,  10s ,  1.00

   The job to be cancelled has job-id ``202169``.

2. Delete the job

   .. code-block:: bash

      [username@furnace ~]$ qdel 202169

3. Are you using a temporary folder on the compute-node (e.g. :ref:`page-queuing-heavyio`)? Be sure to delete all files on the compute node.

   .. code-block:: bash

      # login to the compute-node
      [username@furnace ~]$ ssh compute-0-11

      # go the the user's directory on the hard-disk of the compute-node
      [username@compute-0-11 ~]$ cd /state/partition1/username

      # list all files/directories: shows the temporary directory
      [username@compute-0-11 /state/partition1/username]$ ls

        202169

      # remove the temporary directory
      [username@compute-0-11 /state/partition1/username]$ rm -r 202169

      # logout of the compute-node
      [username@compute-0-11 /state/partition1/username]$ exit

.. note::

  To verify what is left behind on the hard-disks of each of the compute-nodes, from the head-node run

  .. code-block:: bash

    [username@furnace ~] $ rocks run host "ls /state/partition1/`whoami`"

  This scans all the nodes. See also: :ref:`etiquette-monitor-resources-rocks`

What happens if a node runs out of memory?
------------------------------------------

The node will use the hard-disk as additional memory (`swap`). This is such a slow process that it effectively kills the node. A manual reset by the system administrator is needed.

What happens if a node runs out of disk space?
----------------------------------------------

The node cannot write any files (even temporary). The node will shut-down immediately, killing all jobs currently running on it.

Do I only use the CPUs I claim?
-------------------------------

The PBS-directive reserving nodes, for example:

.. code-block:: bash

  #PBS -l nodes=1:ppn=4:intel

helps the scheduler to assign jobs to nodes such that there are enough resources available (in this example 4 CPUs on on Intel-node). However:

1. These CPUs are not neccessarily used.

   * Parallelization is not trivial, and highly problem dependent. Some hints:

     * Matlab: ``parfor``-loop (see also: :ref:`languages-matlab-par`).

     * C/C++ or Fortran: openmpi-library.

   * Verify that the job is parallelized correctly.

     * Check the speed-up as a function of the number of CPUs.

     * Use :ref:`etiquette-monitor-jobs-myqstat`, verify that the ``score`` is approximately 1:

       .. code-block:: bash

         [username@furnace ~]$ myqstat

     * Login to the compute-node, and use ``top`` to monitor the CPU-usage of each process:

       .. code-block:: bash

         [username@furnace ~]$ ssh compute-0-11
         [username@compute-0-11 ~]$ top

2. There is no guarantee that not more than these CPUs are used.

   * Several software-packages by default use the total amount of CPUs available. These are not limited to the amount of CPUs claimed, but correspond to the total number of CPUs in the node. Some hints:

     * :ref:`languages-matlab`: use the ``singleCompThread`` option

.. note::

  Parallellization is accompanied with overhead. If not parallellized properly the computational costs of this additional overhead can out-weigh the benefit of the additional computational power: in the worst case your job can even slow down.

Cheat-sheet
===========

.. contents:: **Categories**
    :local:
    :depth: 2
    :backlinks: top

Queuing system
--------------

========================= =======================================================================================================
Command                   Description
========================= =======================================================================================================
``qsub "PBS-file"``       submit a job, controlled using the PBS-file ``"PBS-file"``
------------------------- -------------------------------------------------------------------------------------------------------
``qdel "job-id"``         delete the job with identifier ``"job-id"``
------------------------- -------------------------------------------------------------------------------------------------------
``qpeek "job-id"``        live-monitor of the PBS-out-file, for the job with identifier ``"job-id"``
------------------------- -------------------------------------------------------------------------------------------------------
``qstat``                 list basic information of all jobs
------------------------- -------------------------------------------------------------------------------------------------------
``qstat -f``              list detailed information of all jobs
------------------------- -------------------------------------------------------------------------------------------------------
``qstat -f "job-id"``     list detailed information of the job with identifier ``"job-id"``
------------------------- -------------------------------------------------------------------------------------------------------
``pbsnodes``              list detailed information of all compute-nodes
------------------------- -------------------------------------------------------------------------------------------------------
``myqstat``               list the most important information for the ``qstat -f`` command
------------------------- -------------------------------------------------------------------------------------------------------
``myqstat -N``            list the most important information for the ``pbsnodes`` command
========================= =======================================================================================================

Monitor processes and resources
-------------------------------

========================= =======================================================================================================
Command                   Description
========================= =======================================================================================================
``top``                   live-monitor of current running processes
------------------------- -------------------------------------------------------------------------------------------------------
``ps``                    show snap-shot of processes
------------------------- -------------------------------------------------------------------------------------------------------
``ps -aux``               show snap-shot of all processes
------------------------- -------------------------------------------------------------------------------------------------------
``du -h``                 size of directories
------------------------- -------------------------------------------------------------------------------------------------------
``df -h``                 total, used, and available disk-space
========================= =======================================================================================================

Directory operations
--------------------

========================= =======================================================================================================
Command                   Description
========================= =======================================================================================================
``pwd``                   print working (current) directory
------------------------- -------------------------------------------------------------------------------------------------------
``mkdir "dir"``           make new directory ``"dir"``
------------------------- -------------------------------------------------------------------------------------------------------
``cd "dir"``              go to directory ``"dir"``
------------------------- -------------------------------------------------------------------------------------------------------
``cd ..``                 go up one directory
------------------------- -------------------------------------------------------------------------------------------------------
``ls``                    list files
------------------------- -------------------------------------------------------------------------------------------------------
``ls -lh``                detailed file information
========================= =======================================================================================================

File-operations
---------------

========================= =======================================================================================================
Command                   Description
========================= =======================================================================================================
``cat "file"``            print file content to the screen
------------------------- -------------------------------------------------------------------------------------------------------
``head "file"``           show first 10 line of the file content
------------------------- -------------------------------------------------------------------------------------------------------
``tail "file"``           show last 10 line of the file content
------------------------- -------------------------------------------------------------------------------------------------------
``cp "file1" "file2"``    copy ``"file1"`` to ``"file2"``
------------------------- -------------------------------------------------------------------------------------------------------
``mv "file1" "file2"``    move (rename) ``"file1"`` to ``"file2"``
------------------------- -------------------------------------------------------------------------------------------------------
``rm "file"``             remove ``"file"``
------------------------- -------------------------------------------------------------------------------------------------------
``rm -r "dir"``           remove ``"dir"``
========================= =======================================================================================================

Bash commands
-------------

========================= =======================================================================================================
Command                   Description
========================= =======================================================================================================
``whoami``                show your username
------------------------- -------------------------------------------------------------------------------------------------------
``man command``           show manual of a ``command`` (sometimes: ``command -h`` or ``command --help``
========================= =======================================================================================================

Search files
------------

========================= =======================================================================================================
Command                   Description
========================= =======================================================================================================
``find``                  find files
------------------------- -------------------------------------------------------------------------------------------------------
``grep``                  show matched pattern in file content
========================= =======================================================================================================

Keyboard shortcuts
------------------

========================= =======================================================================================================
Command                   Description
========================= =======================================================================================================
:kbd:`Ctrl+c`             abort command
------------------------- -------------------------------------------------------------------------------------------------------
:kbd:`Ctrl+r`             search command history (use :kbd:`Ctrl+r` to proceed to next match, and arrows to modify the command)
------------------------- -------------------------------------------------------------------------------------------------------
:kbd:`Ctrl+d`             exit terminal
========================= =======================================================================================================

Advanced job submit
===================

.. contents::
    :local:
    :depth: 2
    :backlinks: top

Submit a batch job
------------------

Consider the following example:

* Each job is a sub-directory of the current path, in this example ``sim0``, ``sim1``, and ``sim2``.

* The job has the ``job.pbs`` file to control the job.

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
    qsub job.pbs;
    cd $froot;
  done

* The Bash-``for``-loop is used to loop over space separated list of names:

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

* The list of jobs to submit is generate using the ``find``-command:

  .. code-block:: bash

    find . -iname 'job.pbs'

  lists

  .. code-block:: bash

    sim0/job.pbs
    sim1/job.pbs
    sim2/job.pbs

* The ``cut``-command is used to split the output of the ``find``-command in the name of the directory

  .. code-block:: bash

    echo $name | rev | cut -d"/" f2- | rev

  by reversing the string, including everything from the first ``/`` onward, and reversing the resulting string to it's original order. This corresponds to including everything up to the last ``/``. In the same way the name of the PBS-file is extracted from the output of the ``find``-command.

* The ``cd``-command is used to proceed to the simulation sub-directory, after which the simulation is submitted. Then ``cd`` is used again to go back to the original directory.

Submit part of a batch job
--------------------------

Consider the following example (similar to above):

* Each job is a sub-directory of the current path.

* The job has the ``job.pbs`` file to control the job.

* A completed job has the file ``pbs.out``, a job not submitted yet does not contain this file.

To submit all jobs that have not yet been submitted:

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

* List the directory names, using the ``find``-command:

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
    check if the file ``pbs.out`` exists. The ``-e`` option comes from the ``test``-command. The ``{}`` is the way to include the search result from the ``find``-command (in this case the sub-directories.

* List the result:

  ``\;``
    terminates the ``find``-command.

  ``-print``
    print the full file name on the standard output, followed by a newline.

Further reading
===============

The following MaTe-TU/e websites provide more information regarding the clusters, the queuing system, or Linux in general:

1. http://faq.wfw.wtb.tue.nl/phpmyfaq.1.5.2
2. http://www.mate.tue.nl/mate/local/software/unix
3. http://www.mate.tue.nl/mate/local/topic.php/57

Other references:

* `Linux cheat sheet <http://overapi.com/linux/>`_