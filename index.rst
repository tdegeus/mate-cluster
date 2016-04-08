
.. topic:: Disclaimer

   Any questions, suggestions, additions, comments, bugs, etc. are most welcome. Please contact us (MaTeCluster@tue.nl). Or directly:

   * Leo Wouters, l.h.g.wouters@tue.nl, GEM-Z 4.17
   * Tom de Geus, t.w.j.d.geus@tue.nl, GEM-Z 4.21
   * Jim Schormans, j.m.j.schormans@tue.nl, GEM-Z 4.13

   The content presented here is meant as example, some adaptation to a specific application is usually needed. We take no responsibility for the loss of data or damage caused by using any of the matters discussed here.

.. topic:: Quick tips

   * Ask students/colleagues/supervisors! People usually have a wealth of experience, which can save you a lot of time.
   * Use relative file-paths anywhere in simulations, this makes it easy to run on your computer and on the cluster. See: ":ref:`sec-bash_cd`".
   * Use :ref:`monitoring_myqstat` to monitor jobs on the cluster. The output is more convenient than that of the default commands.
   * Do not copy-paste scripts from this website, but download them (right-click > Save Link As). Windows has the tendency to mess-up some characters.
   * Be careful that some Windows editors use different line-break characters that Linux (see `Wikipedia <https://en.wikipedia.org/wiki/Newline>`_). To check if everything is as it should be, use the :command:`cat` or :command:`less` command or the :command:`vi` or :command:`nano` editor on the cluster before executing the job (see: :ref:`sec-bash`).
   * Specify the CPU-type on *furnace* (i.e. ``intel`` or ``amd``), but don't specify it on *rng*. The job will not run as the CPU-type field does not exists (all nodes have the same type of CPUs)

This manual is intended as a starting point for people who want to use (the MaTe) clusters. Typically these clusters run on Linux and make use of a queuing system to assign jobs of (different) users to parts of its resources. This manual discusses the :ref:`page-queuing`, including some :ref:`languages`. A basic knowledge of :ref:`sec-linux` and :ref:`sec-bash` is assumed. For those unfamiliar with them an introduction covering the basics is included in :ref:`sec-linux` and :ref:`sec-bash`, respectively.

Note that in any programming language (including Linux/Bash) there are many ways of doing the same thing, and the choice is usually very subjective. We only presented several examples, complemented with pointers on how to learn more.

========
Contents
========

.. toctree::
   :maxdepth: 2

   pages/mate.rst
   pages/queuing.rst
   pages/etiquette.rst
   pages/tips.rst
   pages/linux_bash.rst
   pages/languages.rst

====================
Advanced job control
====================

.. toctree::
   :maxdepth: 2

   pages/myqstat.rst

==================
Indices and tables
==================

* :ref:`genindex`
* :ref:`search`

==============
Acknowledgment
==============

Over time the following people have contributed to the content as presented here:

* Bart Vossen
* Franz Bormann
* Jan Neggers
* Jeroen van Beeck
* Tom de Geus

