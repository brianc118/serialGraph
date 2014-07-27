serialGraph
===========

Python Serial Grapher for Debugging Visualisation

Tested with Arduino, Teensy 3.0, Teensy 3.1.

Works with bluetooth as well (tested with Sparkfun Bluesmirf silver, and JY-MCU)

Simple multithreaded program to read serial data in csv format (i.e. data1,data2,...)
and graph in pyqtgraph. Accepts command line arguments in the form serialGraph.py PORT BAUD
but default parameters will be used in the absence of arguments

The number of columns of the input is automatically determined.

Open source under MIT License (MIT)

Requires Python 3+ with pyqtgraph installed. See http://www.pyqtgraph.org/
