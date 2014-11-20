:tocdepth: 2

.. _languages:

Language specific remarks/examples voor s_tom
=============================================

.. topic:: Help wanted

  Is the language you are (or will be) using not listed? Do you have any remarks and/or extensions? Please help us by contributing to this website.

  Please contact: MaTeCluster@tue.nl

.. contents:: **Outline**
  :local:
  :depth: 3
  :backlinks: top

.. _languages-matlab:

MATLAB
------

The location of ``MATLAB``'s executable is different depending on the cluster.
For example, on ``furnace`` we find the programs installed in

.. code-block:: bash

   /share/apps

In particular, the 2010a version of ``MATLAB`` is located in

.. code-block:: bash

   /share/apps/matlab-2010a/bin/matlab

Because the clusters do not have a display and therefore cannot provide a GUI, ``MATLAB`` has to be started with the proper
options to suppress loading of the ``MATLAB desktop``. To list which options are available, type

.. code-block:: bash

   [username@furnace ~]$  /share/apps/matlab-2010a/bin/matlab -help

Have a look at the available ``MATLAB`` options, especially the ones discussed in this section,
also notice the ``-r`` option, which allows you to execute some ``MATLAB`` code after ``MATLAB`` is started.
To start, for example ``MATLAB r2010a``, on the furnace, use this command:

.. code-block:: bash

   [username@furnace ~]$  /share/apps/matlab-2010a/bin/matlab -nodisplay -singleCompThread

The first option disables all display options within ``MATLAB``, which automatically disables the ``MATLAB`` desktop.
The ``-singleCompThread``  (Available since 2009a, for older versions use the ``maxNumCompThreads(1)``
command in your m-file.) disables automatic parallelization which is required on the cluster, otherwise ``MATLAB`` will
use more cpus than assigned to the job by the queuing system, which will overload the node.

Matlab scripting guidelines
~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Be sure that ``MATLAB`` actually quits, or your job will run forever.
   To this end include the ``quit`` command at the end of your script. Consider the following pbs-file to run
   ``myscript.m``

   .. literalinclude:: scripts/matlab.pbs
      :language: bash

   :download:`source: matlab.pbs <scripts/matlab.pbs>`

2. Because there is no ``MATLAB`` desktop ``MATLAB`` is unable to render any figures. As a result, most commands producing
   figures, like for instance ``plot`` will cause your job the abort prematurely.
   Note, it is possible to create figure-files on the cluster, but this is considered to be outside the scope of this manual.

3. Any output to the command line will slow down your code significantly, it is best to do this as little as possible.

4. Beware of how ``MATLAB`` calculates random numbers, they are based on a seed which in turn is calculated from the time
   that ``MATLAB`` has been running. This means that if you would issue the same job through the queuing system, you will
   get the same random numbers because the time that ``MATLAB`` is running will be equal. To correct for this, the random
   seed needs to be altered. To this end include the following before the random number is used:

   .. code-block:: matlab

       % initiate the random seed
       mySeed = sum(100*clock);
       if verLessThan('matlab','7.7.0') % 2007a or older
         rand(’twister’,mySeed);
       elseif verLessThan('matlab','7.14.0')
         RandStream.setDefaultStream(RandStream('mt19937ar','Seed',mySeed));
       else % newer than 2010b
         RandStream.setGlobalStream(RandStream('mt19937ar','Seed',mySeed));
       end

.. _languages-matlab-par:

Matlab parallelization
~~~~~~~~~~~~~~~~~~~~~~

First, ``MATLAB`` will automatically perform certain operations in parallel (multi-threading), which is undesirable on
the cluster. This is because ``MATLAB`` does not know how many cores you specified for your job, and will use more cores
than assigned to your job by the queuing system. This will overload the node, and will reduce the performance of other
jobs running on the same node, please make sure you disable this feature, by starting matlab with the
``-singleCompThread`` option.

Second, the proper way to run parallel jobs in ``MATLAB`` is by the use of ``parfor``-loops, which are parallel
equivalents of the ``for``-loop. You can always run a ``parfor``-loop even on a single cpu, and play with
the difficulties of programming proper parallel code. The way you assign multiple cpus to the ``parfor``-loop is
by starting a ``matlabpool``. ``MATLAB`` has the capability to directly communicate with the queuing system, but
that requires a very expensive license, which we don't have. Nevertheless, you can start ``local`` matlabpools with up
to 12 workers depending on your ``MATLAB`` version (The limit was 4; this changed to 8 in R2009a; and to 12 in R2011b).
When starting a ``local`` ``matlabpool``, ``MATLAB`` will create a temporary folder in your home folder to manage
this particular pool. This means, that when you start multiple parallel ``MATLAB`` jobs on the cluster, each job will try to
create the same folder, since the home folder is shared among compute-nodes. The circumvent this problem the ``scheduler``
data location can be modified with the ``findResource`` command, see lines 4-6 in the example below:

.. code-block:: matlab

   % number of matlab Workers to use
   cores = 2;

   % check if a matlab pool is already open
   poolsize = matlabpool('size')
   if poolsize == 0
     % no pool is found --> start a new one
     matlabpool(cores);
   end

   n = 1000;
   m = 1000;
   A = zeros(n,m);

   % a parallel for loop
   parfor ( i = 1: n )
     A (i,:) = zeros(1,m);
   end

   % be sure to close the matlabpool
   matlabpool close

Deciding what to put in the ``parfor`` loop is quite difficult. In a  ``parfor`` loop, the loop iterations are processed in a random order by independent ``MATLAB`` workers. First of all, this means that calculations performed inside one loop iteration will not be available in other iterations, this is logical, since the iterations run parallel in random order, so it is impossible to know which iteration is already performed. Second, it means that all the data required inside the iteration will be copied and sent to each worker. It also means that variables which are only defined inside the ``parfor`` loop will not be available outside the loop. ``MATLAB`` will perform a sanity check on your ``parfor`` loop before running and give a reasonably readable error message if something is wrong. However, when ``MATLAB`` encounters an error while processing the ``parfor`` loop, it will only tell you which ``parfor`` loop contained an error. Refer to the ``MATLAB`` manual about the difficulties regarding parallel computing ( http://www.mathworks.nl/help/distcomp/advanced-topics.html ).

.. _languages-marc:

MSC Marc
--------

On furnace the ``MSC Marc`` executable is located in

.. code-block:: bash

   /share/apps

Different versions are available, for example, the executable of the 2005r3 version is located at

.. code-block:: bash

   /share/apps/marc2005r3i/marc2005r3/tools/run_marc

The clusters only provide the ``MSC Marc`` executable, the graphical front-end ``MSC Mentat`` is not installed.

Command line options
~~~~~~~~~~~~~~~~~~~~

Starting a ``MSC Marc`` job involves providing command line options to the ``MSC Marc`` executable. The most important ones, together with their possible arguments, are

.. code-block:: bash

   -q [b|f] -v [y|n] -j jobname -u usersub

where the options are

* ``-q``  run in the ``b`` ackground or ``f`` oreground; on the cluster, **always** run the job in the ``f`` oreground

* ``-v``  verify the input before the job starts, ``y`` es or ``n`` o; **always** select ``n`` o

* ``-j``  input file; this is the ``.dat`` file that can be generated by Mentat

These three options should always be specified. The fourth one, ``u``, specifies an optional user subroutine file, written in ``Fortran``. Other options are listed in the ``run_marc`` script in the ``MSC Marc`` executable directory.

Compiler configuration
~~~~~~~~~~~~~~~~~~~~~~

When using ``Fortran`` subroutines a specific ``Fortran`` compiler needs to be specified. The compiler is used to:

1. Compile the user-subroutine to an "object"-file (e.g. ``mysubroutine.o``).

2. Compile MSC.Marc with this object-file (e.g. ``mysubroutine.o``) to a new executable. This executable is then used to run the simulation (read the dat-file, etc.).

The :command:`run_marc` command takes care of this, including setting the compiler-options and environment variables, and including libraries.

Different versions of ``MSC Marc`` require a different ``Fortran`` compiler version, all of them Intel (the GNU-compiler is not supported). Unfortunately it is not completely clear which compiler to use with which version of ``MSC Marc``. The following combinations seem to work; ``MSC Marc`` 2005r3, 2008r1, 2010: ``Intel`` compiler v10, ``MSC Marc`` 2011, 2012, 2013: ``Intel`` compiler v12. Other combinations might also work, e.g. ``MSC Marc`` 2005r3 in combination with the
``Intel`` compiler v8.

It is common to specify the ``Fortran`` compiler in the :file:`~/.bashrc` file, such that it becomes the default. The different compilers and commands are

======= ==========================================================================
Version Add this line to :file:`.bashrc`
======= ==========================================================================
v8      :command:`source /share/apps/intel_fce_80/bin/ifortvars.sh`
v9      :command:`source /opt/intel/fce/9.1.037/bin/ifortvars.sh`
v10     :command:`source /opt/intel/fce/10.1.011/bin/ifortvars.sh`
v12     :command:`source /share/apps/intel/composerxe/bin/compilervars.sh intel64`
======= ==========================================================================

An example Marc job
~~~~~~~~~~~~~~~~~~~

Since ``MSC Marc`` jobs typically involve a lot of disk access, it is strongly recommended to use the script for the :ref:`page-queuing-heavyio`. Consider the example below, for which it is remarked that it is necessary that the ``MSC Marc`` input file (``.dat``) and, if needed, user ``Fortran`` subroutines are in the same directory as the ``.pbs`` script. This can of course be changed.

.. literalinclude:: scripts/marc.pbs
   :language: bash

:download:`source: marc.pbs <scripts/marc.pbs>`

Marc parallelization
~~~~~~~~~~~~~~~~~~~~

The most common method to parallelize ``MSC Marc`` is by domain decomposition, i.e. the FE domain is split in multiple subdomains and each subdomain is assigned to a cpu-core. For relatively small models (e.g. < 10.000 degrees of freedom), parallelization is not recommended because of the overhead involved with it. For domain decomposition some more considerations need to be made. First, one needs to make sure that the solution is not impacted by the domain decomposition scheme. Secondly, several features, such as remeshing, do not work in the domain decomposition mode. For more unsupported features, see manual volume A. Thirdly, subroutines (e.g. ``impd.f``) may not work correctly in domain decomposition mode. 

The domain decomposition parallelization is flagged through a command line option: ``-nprocds 4``, where 4 is the number of cpu-cores to use in this case. To prevent mistakes in assigning the number of cpu-cores, the best way to adapt your ``.pbs`` is to add

.. code-block:: bash

   ncpus=`cat $PBS_NODEFILE | wc -l`

to line 9 of the single core ``MSC Marc`` script, and change the ``MSC Marc`` executable line (34) to

.. code-block:: bash

   $marc -q f -v n -j mymarcjob -u myusersub -nprocds $ncpus

Now you only need to specify the number of cpu-cores to use in the PBS directive (line 5) and your simulation will automatically be run on the number of cores you reserved for your job.

The latest ``MSC Marc`` versions (2011 and up) will automatically set the number of parallel threads equal to the number of domains, which is undesired behavior. This will cause the job to start :math:`N` processes (one for each subdomain) and within each process, start :math:`N` threads (for the solver step). This will overload the node and will reduce the performance of all jobs running on the node, also the jobs of other users. A clear fingerprint of this problem is when the compute-node load exceeds the number of CPUs of the node (on the furnace: 8 for intel, 24 for amd). The solution is simple, manually set the number of threads to one:

.. code-block:: bash

   $ marc -q f -v n -j mymarcjob -u myusersub -nprocds $ncpus -nthread 1

The default setting for ``MSC Marc`` is to generate one post (.t16) file for each domain, i.e. for each CPU-core.
Usually this is not the desired behavior, you would like to have a single output file where all the domains are combined. To achieve this you need to change a parameter in the input (.dat) file. Locate the line that says ``post`` and in the ``next`` line, change the 5th number to 2. No more changes need to be made to generate a single output file.

If domain decomposition is not an option and parallelization is still preferred, another option is to apply parallel solving.
This option is only available in newer ``MSC Marc`` versions.

Marc and Python
~~~~~~~~~~~~~~~

``Marc`` (actually ``Mentat``) is supplied with a set of \textsc{Python} modules. There are two major libraries, one is for creating input files, i.e. to replace/augment ``Mentat``, the second is for reading ``Post`` files (``.t16`` or ``.t19`` files). The latter can be a good replacement of the use of subroutines like ``elevar``, or ``impd``, especially when using domain decomposition.

There is a separate manual for the ``Python`` modules and is named e.g. ``marc_2012_doc_python.pdf`` (i.e. not A to E). The manual is quite nice and is a good reference to the python commands provided by the libraries. To start a ``Mentat-Python`` script it is important that the environment variables are set properly which is handled by the ``run_python`` script which is inside the ``../mentat*/bin`` folder. ``run_python`` will set all
required environment variables such that the ``Mentat-Python`` modules can be imported and then either opens a python terminal or runs a python script, for example

.. code-block:: bash

   $ /share/apps/marc2012/mentat2012/bin/run_python
   $ /share/apps/marc2012/mentat2012/bin/run_python mypythonscript

On a cluster, it is impossible to run ``Mentat`` because it has no display, therefore, ``Mentat`` is typically not installed. At the time of writing only ``Mentat2012`` is installed with the ``Mentat`` executable disabled. Ask `Leo Wouter <l.h.g.wouters@tue.nl>` if you require the use of the ``Mentat-Python`` modules of other versions of ``Marc-Mentat``. Remember that version 2012 can probably also handle ``Post``-files created by older ``Marc`` versions.

.. _languages-fortran:

Fortran
-------

``Fortran``-codes (with the exception of ``Abaqus`` or ``MSC Marc`` subroutines) are mostly specialized, and therefore are outside the scope of this manual. Only a short introduction is given.

Example Fortran job
~~~~~~~~~~~~~~~~~~~

``Fortran`` code can be compiled on the cluster before it is executed. Consider the following example.

.. literalinclude:: scripts/fortran.pbs
   :language: bash

:download:`source: fortran.pbs <scripts/fortran.pbs>`

Fortran parallelization
~~~~~~~~~~~~~~~~~~~~~~~

``Fortran`` code can be compiled to run on multiple cores. There is one issue: when not done correctly, the compiled program
will try to use all the cores in the node, even if you did not reserve them. This means that you can seriously harm other
people's jobs. To prevent this you need to make some small changes to the ``.pbs`` script.

.. literalinclude:: scripts/fortranparallel.pbs
   :language: bash

:download:`source: fortranparallel.pbs <scripts/fortranparallel.pbs>`


