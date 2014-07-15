"""
Simple multithreaded program to read serial data in csv format (i.e. data1,data2,...)
and graph in pyqtgraph. Accepts command line arguments in the form serialGraph.py PORT BAUD
but default parameters will be used in the absence of arguments

The number of columns of the input is automatically determined.

Open source under MIT License (MIT)

Copyright (c) 2014 Brian C

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


import sys
import serial
import threading
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
from collections import Counter
from datetime import datetime


if len(sys.argv) == 1:
    # default parameters. Modify as needed or just use command line arguments
    port = 'COM20'
    baud = 9600
elif len(sys.argv) == 3:
    port = sys.argv[1]
    baud = int(sys.argv[2])
else:
    # incorrect argv syntax
    print("incorrect arv ... exiting")
    sys.exit()

# pgm info
pgm_version = '0.1'

# global variables that you should not modify
data = []
numberOfElements = 0
connected = False

# function to get mode of list
def mode(nums):
    c = Counter(nums)
    return c.most_common(1)[0][0]
    
def serialParser(ser):
    global data
    global numberOfElements
    buff = ''
    initialised = False
    print("Determining number of data columns")
    i = 0
    initialiseData = []
    while i < 50:
        if(ser.inWaiting() > 0):
            i = i+1
        buff += ser.read(ser.inWaiting()).decode("utf-8")
        lines = buff.splitlines(True)  # split lines and keep newline characters
        buff = ''
        
        for eachLine in lines:
            if "\n" in eachLine:
                initialiseData.append((eachLine.count(',') + 1))
            else:
                # incomplete line
                buff += eachLine
    if(len(initialiseData) is not 0):
        numberOfElements = mode(initialiseData)
        initialised = True
        print("Found %d elements" % numberOfElements)
    else:
        print("could not find any useful data")
    
    buff = ''
    initTime = datetime.now()
    if initialised:
        for i in range(numberOfElements + 1):   # we actually need an extra list for times
            data.append([])
            
        while True:
            # check if there is serial data waiting
            if ser.inWaiting() > 0:   
                buff += ser.read(ser.inWaiting()).decode("utf-8")
                lines = buff.splitlines(True)  # split lines and keep newline characters
                buff = ''
                for eachLine in lines:
                    if "\n" in eachLine:     
                        # check if number of elements is correct
                        if (eachLine.count(',') + 1) == numberOfElements:
                            appendingRow = []
                            # complete line. Split and add to data
                            t = datetime.now() - initTime
                            appendingRow.append(t.total_seconds() * 1000)
                            for numStr in eachLine.split(','):
                                try:
                                    appendingRow.append(float(numStr))
                                except:
                                    break
                            # serial input is correct. We can now safely add this to the data for graphing
                            
                            for i in range(numberOfElements + 1):
                                data[i].append(appendingRow[i])
                            print(appendingRow)
                    else:
                        buff += eachLine        
                            # incomplete line
        
    print("exiting serial thread")

def plot():
    pg.setConfigOptions(antialias=True)    
    window = pg.GraphicsWindow(title = 'serialGraph ' + pgm_version + 'by Brian C')
    graph = window.addPlot(title = "serialGraph")
    graph.addLegend()
    while True:
        # clear plot first
        graph.clear()
        # plot data
        for i in range(numberOfElements):   
            graph.plot(data[0], data[i+1], clear = False,pen=(i,numberOfElements), name = "Column " + str(i + 1))
        
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):            
            pg.QtGui.QApplication.processEvents()

if __name__=='__main__':
    print("attempting connection to %s at baud %d" % (port, baud))    
    try:
        # connect to serial port
        serial_port = serial.Serial(port, baud, timeout=0)
    except:
        e = sys.exc_info()
        serial_port = None
        print("error connecting to serial")
        print(e)
        while True:
            pass
    if serial_port != None:
        print("starting serial thread")
        # begin serial parsing thread
        serialThread = threading.Thread(target=serialParser, args=(serial_port,))
        serialThread.start()
        # wait until serial thread determines the number of columns (or numberOfElements)
        while numberOfElements == 0:
            pass
        
        print("Starting graph")
        # begin plot thread
        plotThread = threading.Thread(target=plot)
        plotThread.start()
    