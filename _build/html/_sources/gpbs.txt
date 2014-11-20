:tocdepth: 2

.. _gpbs:

#######
myqstat
#######

.. contents:: **Outline**
  :depth: 3
  :backlinks: top

**************************
Detailed usage information
**************************


********************
Download and install
********************

**********************
Implementation details
**********************

.. note::

  You are more than welcome to contribute to the implementation of ``myqstat`` and/or ``gpbs``. Please contact `Tom de Geus <t.w.j.d.geus@tue.nl>`_

myqstat: user frontend
======================

gpbs - Python module
====================

.. image:: images/under_construction.png
   :align: center
   :width: 30%


Main usage
----------

1.  Read individual job information::

      import gpbs

      jobs = gpbs.qstatRead()

    This command reads the information from the ``qstat -f`` command and stores
    it as a list of individual jobs (of the ``Job``-class).

2.  Read basic compute-node information::

      import gpbs

      nodes = gpbs.pbsRead(ganglia=False)

    This commands read the information from the ``pbsnodes`` command and stores
    it as a list of individual compute-nodes (of the ``Node``-class).

3.  Read detailed compute-node information::

      import gpbs

      nodes = gpbs.pbsRead()

    This commands read the information from the ``pbsnodes``, and the
    ``ganglia ...`` command and stores it as a list of individual compute-nodes
    (of the ``Node``-class). Notice: the ganglia command is slow, as it needs
    to connect to each of the individual nodes.

Class overview
--------------

Job-class
^^^^^^^^^

Job information. The class has the following key-fields.

=========== =========== ========================================================
field       type        description
=========== =========== ========================================================
id          <int>       id
name        <str>       name
owner       <str>       owner
state       <str>       state (Q,R)
host        <Host>      host(s) (compute-node(s))
resnode     <ResNode>   reserved resources (CPUs) (e.g. "2:4:i")
memused     <Data>      memory usage
cputime     <Time>      CPU time used
walltime    <Time>      actual runtime
score       <float>     score (CPU time over walltime)
=========== =========== ========================================================

Node-class
^^^^^^^^^^

Compute node information. The class has the following key-fields.

=========== =========== ========================================================
field       type        description
=========== =========== ========================================================
name        <str>       name of the compute-node
node        <int>       node number (compute-0-X -> int(X))
state       <str>       status (free,job-exclusive,down,offline)
ncpu        <int>       number of CPUs
ctype       <str>       type of node (intel,amd)
jobs        <lst>       list of job numbers <int>
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
