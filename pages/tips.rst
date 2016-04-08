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

   .. code-block:: none

      [username@furnace ~]$ myqstat

      ID   Owner    Job name  Host  CPUs  Mem pmem  S  Time  Score
      ===  =======  ========  ====  ====  === ====  =  ====  =====
      690  tdegeus  job.pbs     17   1:1  1gb  2gb  R  7.2m   0.99

   The job to be cancelled has job-id ``690``.

2. Delete the job

   .. code-block:: bash

      [username@furnace ~]$ qdel 690

3. Are you using a temporary folder on the compute-node (e.g. :ref:`page-queuing-heavyio`)? Be sure to delete all files on the compute node.

   .. code-block:: bash

      # login to the compute-node
      [username@furnace ~]$ ssh compute-0-11

      # go the the user's directory on the hard-disk of the compute-node
      [username@compute-0-11 ~]$ cd /state/partition1/username

      # list all files/directories: shows the temporary directory
      [username@compute-0-11 /state/partition1/username]$ ls

        690

      # remove the temporary directory
      [username@compute-0-11 /state/partition1/username]$ rm -r 690

      # logout of the compute-node
      [username@compute-0-11 /state/partition1/username]$ exit

.. note::

  To verify what is left behind on the hard-disks of each of the compute-nodes, from the head-node run

  .. code-block:: bash

    [username@furnace ~] $ rocks run host "ls /state/partition1/`whoami`"

  This scans all the nodes. See also: :ref:`etiquette-monitor-resources-rocks`

.. note::

  To delete a job, a batch of jobs, or all the user's jobs, the ``qdelall``-command is available. This script can also remove the temporary directory on the compute-node. See: :ref:`monitoring`, and ``qdelall --help``.

What happens if a node runs out of memory?
------------------------------------------

The node will use the hard-disk as additional memory (`swap`). This is such a slow process that it effectively kills the node. A manual reset by the system administrator is needed. All jobs on the node (also those of other users) are killed in the process.

What happens if a node runs out of disk space?
----------------------------------------------

The node cannot write any files (even temporary). The node will shut-down immediately, killing all jobs currently running on it.

Do I only use the CPUs I claim?
-------------------------------

The PBS-directive reserving nodes, for example:

.. code-block:: bash

  #PBS -l nodes=1:ppn=4

helps the scheduler to assign jobs to nodes such that there are enough resources available (in this example 4 CPUs). However:

1. These CPUs are not necessarily used.

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

     * Include ``export OMP_NUM_THREADS=1`` in the ``~/.bashrc``-file to set the default number of threads for OpenMPI programs to one. This default can be overwritten per process (job).

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
``qpeek "job-id"``        monitor of the PBS-out-file, for the job with identifier ``"job-id"`` (NB some delay)
------------------------- -------------------------------------------------------------------------------------------------------
``qstat``                 list basic information of all jobs
------------------------- -------------------------------------------------------------------------------------------------------
``qstat -f``              list detailed information of all jobs
------------------------- -------------------------------------------------------------------------------------------------------
``qstat -f "job-id"``     list detailed information of the job with identifier ``"job-id"``
------------------------- -------------------------------------------------------------------------------------------------------
``pbsnodes``              list detailed information of all compute-nodes
------------------------- -------------------------------------------------------------------------------------------------------
``myqstat``               list the most important information from the ``qstat -f`` command in an easy to read format
------------------------- -------------------------------------------------------------------------------------------------------
``myqstat -N``            list the most important information for the ``pbsnodes`` command in an easy to read format
------------------------- -------------------------------------------------------------------------------------------------------
``myqstat -U``            summarize the users' jobs
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
``ls -lh``                list files, with detailed file information
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

Further reading
===============

The following MaTe-TU/e websites provide more information regarding the clusters, the queuing system, or Linux in general:

1. http://faq.wfw.wtb.tue.nl/phpmyfaq.1.5.2
2. http://www.mate.tue.nl/mate/local/software/unix
3. http://www.mate.tue.nl/mate/local/topic.php/57

Other references:

* `Linux cheat sheet <http://overapi.com/linux/>`_
