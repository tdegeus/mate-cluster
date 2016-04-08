:tocdepth: 2

.. _etiquette:

########################
Monitoring and etiquette
########################

.. contents:: **Outline**
  :local:
  :depth: 1
  :backlinks: top

As the cluster is shared by many users extra responsibility is demanded from users. Currently, the scheduler is configured very openly, i.e. little restrictions are set. This gives users a lot of freedom, allowing exotic jobs, but also demands responsibility. Several fair usage considerations are found below.

.. warning::

  If the nodes run out of resources, other jobs are harmed. When the jobs runs out of:

  * **CPUs**: all jobs slow down considerably.

  * **Memory**: the node crashes, all jobs running on it fail.

  * **Disk-space**: the node cannot write any files, including files of the operating system. The node crashes, all jobs running on it fail.

  * **Network**: all jobs on all nodes slow down considerably, copying operations of all jobs can fail.

Understand your own scripts
===========================

Be careful in recycling scripts (of somebody else). Make sure you understand all the details, ask for help if needed.

Claim what you use and use what you claim
=========================================

Specify all the resources you need, but specify them as close as possible to your job. This can be checked while the job is running, see: :ref:`etiquette-monitor-jobs`. Typical resources claimed:

* CPUs (and compute-nodes):

  .. code-block:: bash

    #PBS -l nodes=1:ppn=1

  NB. On *furnace* two types of nodes are available: Intel and AMD. The Intel-nodes are considerably faster than the AMD-nodes. The latter are mostly useful for parallelization or heavy-memory jobs. To request one of the two, use:

  .. code-block:: bash

    #PBS -l nodes=1:ppn=1:intel
    #PBS -l nodes=1:ppn=1:amd

* Memory:

  .. code-block:: bash

    #PBS -l pmem=1gb
    #PBS -l pvmem=1gb

  The ``pmem`` option gives the scheduler information on the expected memory usage. This way, moderate-memory jobs can be used to compensate for heavy-memory jobs on one node. The ``pvmem`` option makes sure that the jobs fails when the memory usage exceeds the memory claimed.

  .. note::

    Always use these options if your job uses more than roughly "1gb" of memory.

Limit network traffic
=====================

Jobs that have many file operations (reading and/or writing of input/output files) should use a temporary folder on the compute-node rather than reading/writing to/from the head-node through the internal network (see :ref:`page-queuing-heavyio`). If this is omitted the entire cluster will be impaired as the network bandwidth of the head node will be completely filled by read/write operations of these processes.

Software packages that always require this:

* Abaqus

* :ref:`languages-marc`

.. _etiquette-monitor-jobs:

Monitor jobs
============

One of the most critical responsibilities is to actively monitor all your jobs on the cluster. This avoids killing (part of) the cluster, and helps to *"claim what you use and use what you claim"*. There are several way to do this, for example

* The :ref:`etiquette-monitor-jobs-myqstat` command.

* :ref:`etiquette-monitor-jobs-top`.

* The ganglia website. For example: `http://furnace.wfw.wtb.tue.nl/ganglia <http://furnace.wfw.wtb.tue.nl/ganglia>`_

.. _etiquette-monitor-jobs-myqstat:

myqstat
-------

The ``myqstat`` command provides the most relevant information about running (or queued) jobs. For example:

.. code-block:: bash

  [username@furnace ~]$ myqstat

  ID   Owner    Job name  Host  CPUs  Mem pmem  S  Time  Score
  ===  =======  ========  ====  ====  === ====  =  ====  =====
  690  tdegeus  job.pbs     17   1:1  1gb  2gb  R  7.2m   0.99

Each row in the output corresponds to an individual job, in this example only one job is running. The columns provide information about the job:

* ``ID``: the unique job-identifier.

* ``Owner``: the owner of the job (the username of the user that has submitted the job).

* ``Job name``: the name of the job:

  * set by the ``-N`` option (in this example ``-N "myjob"``),

  * if this option was not used, it corresponds to the name of the PBS-file.

* ``Host``: the compute-node on which the job is running.

* ``CPUs``: the amount of CPU-resources reserved by the ``-l`` option (in this example  ``-l nodes=1:ppn=1``).

* ``Mem``: the amount of memory currently used by the job.

* ``pmem``: the amount of memory requested by the ``-l`` option (in this example ``-l pmem=2gb``).

* ``S``: status of the job, can be ``R`` for running, ``Q`` for queued, ``C`` for completed, or ``E`` for erroneous.

* ``Time``: the time that the job has been running (i.e. the "walltime").

* ``Score``: the ratio between the time that the reserved processors have been in use and the time that these processes where claimed for the job.

From this output to most important things to monitor are:

* The **memory usage**. The amount of memory used by all jobs on the node should never exceed the amount of memory present, otherwise the node is killed. To optimally use the memory:

  * use the ``-l pmem="..."`` option whenever your job uses more than ``1gb`` of memory,

  * verify that the actual memory usage does not exceed the requested amount.

* The **score**. The score is defined such that an "optimal" job receives a score of 1. If the score:

  * << 1: the CPUs spend most time waiting for a process. This can occur when more CPUs have been reserved than used by the job, or when the job has been inefficiently parallelized.

  * > 1: the job is using more CPUs than reserved for the job. This slows down all other jobs on the compute-node. This may occur when the job has been inappropriately parallelized.

To obtain more information about the job available to the queuing system use:

.. code-block:: bash

  [username@furnace ~]$ myqstat -f jobid  # information for a specific job-id

For the example above

.. code-block:: bash

  [username@furnace ~]$ myqstat -f 690

.. note::

  The ``myqstat`` command is available for all users.

.. _etiquette-monitor-jobs-top:

System monitor
--------------

To verify that the job is running the expected processes (and only these resources) common Linux system monitoring methods can be applied. In the case that the job is doing something unexpected, for example uses much more (or less) memory or obtains a score much different than 1, this is usually the first start.

The first step is to login to the compute-node. For the example above:

.. code-block:: bash

  [username@furnace ~]$ compute-0-11

where ``11`` should be modified to the job-host. The next step uses:

* The ``top`` command is used to monitor the most important processes running on the node:

  .. code-block:: bash

    [username@compute-0-11 ~]$ top

  use ``q`` to exit.

* The ``ps`` command to list all the (user's) processes:

  .. code-block:: bash

    [username@compute-0-11 ~]$ ps

  To list all the user's processes on the compute-node:

  .. code-block:: bash

    [username@compute-0-11 ~]$ ps aux | grep `whoami`

Monitor resources
=================

An important part of monitoring jobs is to monitor the status (or "health") of the compute-nodes that are being used by the jobs. If for example your job is using a significant amount of memory and another job (of another user) that also uses a lot of memory is assigned to the same compute-node, the node may run out-of-memory, thus failing all jobs running on that node. When properly monitored, a job that has not been running a long time can be killed by user intervention, thus avoiding killing all other jobs. Furthermore, it is important to monitor the amount of resources claimed with respect to the availability to avoid clogging-up the cluster, thus blocking other users. There are three ways of monitoring resources:

* The :ref:`etiquette-monitor-resources-myqstat` command or ``pbsnodes`` command  (discussed below).

* The cluster's website

  `furnace.wfw.wtb.tue.nl/ganglia <http://furnace.wfw.wtb.tue.nl/ganglia>`_

* Logging in to the compute-node, and for example:

  .. code-block:: none

    [username@furnace ~]$ ssh compute-0-11

    [username@compute-0-11 ~]$ df -h      # free disk space
    [username@compute-0-11 ~]$ du -hs *   # directory size
    [username@compute-0-11 ~]$ top        # system monitor

.. _etiquette-monitor-resources-myqstat:

myqstat -N
----------

The ``myqstat -N`` command is a wrapper of the ``pbsnodes`` command. It lists the state and the total, used, and available resources of each of the compute-nodes. A typical output is as follows:

.. code-block:: none

  [username@furnace ~]$ myqstat -N

  Node  State          Ctot  Cfree  Score  Mtot   Mem%
  ====  =============  ====  =====  =====  =====  ====
     0  free             16     16   1.00  265gb  0.01
     1  free             16     15   0.99  265gb  0.01
  -----------------------------
  number of CPUs total    :  32
  number of CPUs offline  :   0
  number of CPUs online   :  32
  number of CPUs working  :   1

The rows correspond to individual compute-nodes. The columns denote:

* ``Node``: the node-number of the compute-node.

* ``State``: the status of the compute-node, for example:

  * ``free``: one of more CPUs available for new jobs,

  * ``job-exclusive``: all CPUs are in use for jobs,

  * ``down``: down for maintenance,

  * ``offline``: down for maintenance.

* ``Type``: CPU-type (on *furnace*: ``amd`` or ``intel``, on *rng* the type does not exist).

* ``Ctot``: total number of CPUs in the node.

* ``Cfree``: number of CPUs available for new jobs.

* ``Score``: the ratio of time that the reserved processors have been in use and the time that these processes where claimed by jobs. Should be around 1, otherwise there is potential misuse, see :ref:`etiquette-monitor-jobs-myqstat`.

* ``Mtot``: total amount of memory in the node.

* ``Mem%``: relative amount of memory used by jobs on the node. If this value reaches 1 the node is killed.

Below the list of nodes an overall summary is available, that can be used to compare the used resources to the total amount of available resources.

This **does not** list the amount of hard-disk space still available, or the amount of data sent over the internal network by jobs. Therefore information from the ``ganglia`` command can be included in the output as follows:

.. code-block:: none

  [username@furnace ~]$ myqstat -N --long

  Node  State          Ctot  Cfree  Score  Mtot   Mem%  HDtot  HD%   Network
  ====  =============  ====  =====  =====  =====  ====  =====  ====  =======
     0  free             16     16   1.00  265gb  0.01    1tb  0.28    316b
     1  free             16     15   0.99  265gb  0.01    1tb  0.09    263b
  ...

This list the additional columns:

* ``HDtot``: total amount of disk-space in the node.

* ``HD%``: ratio of disk-space used on the node. If this value reaches 1, the node is killed (immediately).

* ``Network``: total amount of data sent over the network each second.

.. note::

  This command can be slow as the underlying ``ganglia``-command sometimes has to get the information by logging on to each of the compute-nodes.

Limit disk-usage
================

User-data on the head-node
--------------------------

Move your data from the cluster to your own computer when your jobs are done. Although there is a lot of harddisk space available on the cluster, the disks can and do get full, blocking other users from using the cluster. You can check the amount of free disk space by typing ``df -h`` (on the head node) and check the amount of free space on the line that says ``/state/partition1``. You can check the amount of space you are using by typing ``du -sch *`` from your home directory.

.. _etiquette-monitor-resources-rocks:

User-data on compute-nodes
--------------------------

Besides the "home" folder on the head-node, user-data can be located on the hard-disks of the individual compute-nodes. This data can be the temporary data of running jobs, copied to limit network traffic and optimize the job performance (see :ref:`page-queuing-heavyio`). However when jobs have failed *without* copying and removing the temporary data, the temporary data is left behind on the compute-node. This is highly unwanted as it is of no use, but frequently forgotten. To delete this data:

* Log on to the compute node by typing

  .. code-block:: bash

    [username@furnance ~]$ ssh compute-0-n

  where ``n`` should be replaced by the number of the compute-node. Then clean up your files in the ``/state/partition1`` directory.

  .. warning::

     When a user logs in on the compute-node the current folder is always the mounted home folder (on the head-node), i.e. ``/home/username/`` rather than the local ``/state/partition1/username`` folder.

  .. note::

    This can be done in one command, for example:

    .. code-block:: bash

      [username@furnace ~]$ ssh compute-0-16 'rm -r /state/partition1/`whoami`/188370'

* Manually logging in to each of the compute-nodes that you have used for running calculations is a time-consuming task. An easier route is to run the following command, which checks each compute-node for the existence of the user folder and its contents:

  .. code-block:: bash

    [username@furnace ~]$ rocks run host "ls /state/partition1/`whoami`"

  To suppress warnings, use for example grep:

  .. code-block:: bash

    [username@furnace ~]$ rocks run host "ls /state/partition1/`whoami`" | grep -v "Warning" | grep -v "xauth" | grep -v "No such file or directory"

  The output shows any left behind data. If no jobs are running, it should therefore be empty.




