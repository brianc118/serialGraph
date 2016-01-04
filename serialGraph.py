"""
Simple multithreaded program to read serial data in csv format 
(i.e. data1,data2,...) and graph in pyqtgraph. Accepts command line arguments 
in the form serialGraph.py PORT BAUD or serialGraph.py PORT BAUD DELIMITER
but default parameters will be used in the absence of arguments

Note this program is quite slow for large amounts of data, however for basic 
logging such as PID variable monitoring (at a few hundred Hz) for a few dozen
seconds should be fine. Frame rate drops dramatically as the number of data
points goes past half a million.

The number of columns of the input is automatically determined.

Bugs:
- Program gets laggy when dragging/resizing window
- fps calculations are wrong for some reason

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
import msvcrt
import pyqtgraph as pg
import numpy as np
import msvcrt as m
from serial.tools import list_ports
from pyqtgraph.Qt import QtCore, QtGui
from collections import Counter
from datetime import datetime
from PyQt4 import Qt
# from pyqtgraph.ptime import time
import time

import numpy as np

printRawEnabled = False
printingEnabled = False
logEnabled = True
filterEnabled = False

# default parameters. Modify as needed or just use command line arguments
port = 'COM3'
baud = 115200
delimiter = '\t'
maxRange = 30000000000
minRange = -30000000000
sampleSize = 1000
dataMode = 1

# pgm info
pgm_version = '0.3'

# global variables that you should not modify
data = []
dataReady = False
numberOfElements = 0
connected = False
initialised = False
fps = None
points = 0
pgmExit = False
plotting = False

# def initPlot():
pg.setConfigOptions(antialias=True)    
window = pg.GraphicsWindow(size = (1920,1080), title = 'serialGraph ' + pgm_version + ' by Brian C')

print("Starting graph")

graph = window.addPlot(title = "serialGraph")
graph.addLegend()


def help():
    print ("Parameters are:")
    print ("serialGraph.py PORT BAUD")
    print ("serialGraph.py PORT BAUD DELIMITER")
    print ("serialGraph.py PORT BAUD DELIMITER SAMPLESIZE")

# command line arguments
if len(sys.argv) != 1:
    if sys.argv[1] == "-h" or sys.argv[1] == "-help" or sys.argv[1] == "help":
        help()
        sys.exit()
    elif len(sys.argv) == 3:
        port = sys.argv[1]
        baud = int(sys.argv[2])
    elif len(sys.argv) == 4:
        port = sys.argv[1]
        baud = int(sys.argv[2])
        delimiter = sys.argv[3]
    elif len(sys.argv) == 5:
        port = sys.argv[1]
        baud = int(sys.argv[2])
        delimiter = sys.argv[3]
        dataMode = int(sys.argv[4])
    else:
        # incorrect argv syntax
        print("incorrect syntax")
        help()
        sys.exit()


# function to get mode of list
def mode(nums):
    c = Counter(nums)
    return c.most_common(1)[0][0]
    
def serialParser(ser):
    global pgmExit
    global dataReady
    global data
    global numberOfElements
    global points
    global initialised
    global plotting
    
    buff = ''
    print("Determining number of data columns")
    i = 0
    initialiseData = []
    
    initTime = time.time()
    while i < 50:
        buff += ser.read(ser.inWaiting()).decode("utf-8")
        lines = buff.splitlines(True)  # split lines and keep newline characters
        buff = ''
        for eachLine in lines:
            if "\n" in eachLine:
                initialiseData.append((eachLine.count(delimiter) + 1))
                i = i+1
                if printingEnabled:
                    print("%d\t%d\t%s" % (i, eachLine.count(delimiter), eachLine))
            else:
                # incomplete line
                buff += eachLine
        if time.time() - initTime > 5:
            print("Timeout")
            initialiseData = []
            break
    if(len(initialiseData) is not 0):
        numberOfElements = mode(initialiseData)
        # no use of initialiseData anymore
        del initialiseData        
        
        initialised = True
        print("Found %d elements" % numberOfElements)
    else:
        pgmExit = True
        print("Could not find any useful data. Exiting")
    
    # open logfile if enabled
    if logEnabled:
        file = open('Log.csv', 'w')
        
    lNum = []
    
    for i in range(numberOfElements):
        lNum.append(0)
    
    lineCount = 0
    #initialise buff
    buff = ''
    
    #initialise time
    initTime = datetime.now()
    disconectTime = initTime
    if initialised:
        for i in range(numberOfElements + 1):   # we actually need an extra list for times
            data.append([])
            
        while True:
            # check if there is serial data waiting
            # if (ser.inWaiting() > 0 and dataReady is False):
            waiting = 0
            try:
                waiting = ser.inWaiting()
                disconectTime = datetime.now()
            except:
                if (datetime.now() - disconectTime).total_seconds() > 2:
                    print("Disconnected")
                    pgmExit = True
                waiting = 0
                
            if (waiting > 0):   
                serData = ser.read(ser.inWaiting()).decode("utf-8")
                buff += serData
                lines = buff.splitlines(True)  # split lines and keep newline characters
                buff = ''
                for eachLine in lines:
                    if "\n" in eachLine:     
                        # check if number of elements is correct
                        if (eachLine.count(delimiter) + 1) == numberOfElements:
                            goodData = True
                            lineCount = lineCount + 1
                            appendingRow = []
                            # complete line. Split and add to data
                            t = datetime.now() - initTime
                            appendingRow.append(t.total_seconds() * 1000)

                            if printRawEnabled:
                                print(eachLine)

                            i = 0
                            for numStr in eachLine.split(delimiter):
                                try:
                                    num = float(numStr)
                                    if num > maxRange or num < minRange:
                                        num = lNum[i]
                                    else:
                                        lNum[i] = num
                                    appendingRow.append(num)
                                    
                                    i = i + 1
                                    
                                except:
                                    goodData = False
                                    break
                            # serial input is correct. We can now safely add this to the data for graphing
                            if goodData:
                                while plotting == True:
                                    print("pass")
                                    pass
                                dataReady = False
                                for i in range(numberOfElements + 1):
                                    data[i].append(appendingRow[i])
                                    
                                # Data ready for graphing. 
                                points = points + numberOfElements + 1
                                # Assign dataReady to true to allow plotting thread to plot
                                dataReady = True
                                if printingEnabled:
                                    print(appendingRow)
                                if logEnabled:
                                    for i in range(numberOfElements):
                                        file.write(str(appendingRow[i]))
                                        file.write(',')
                                        
                                    file.write(str(appendingRow[numberOfElements]))
                                    file.write('\n')
                           
                    else:
                        buff += eachLine        
                            # incomplete line
        
    print("exiting serial thread")

def updatePlot():
    global plotting
    global pgmExit
    global dataReady
    global fps
    global points
    global numberOfElements
    if dataReady:  
        print("Update %f" % time.time())
        plotting = True  
        myData = data[:]
        # time.sleep(0.5)
        plotting = False
        
        # clear plot first
        graph.clear()
        # remove legends. See https://groups.google.com/forum/#!msg/pyqtgraph/UTwLwC5mQnQ/PVZkt1-2OrQJ
        graph.legend.items = []
        # plot data
        if dataMode == 0:
            for i in range(numberOfElements):   
                # this is often the suspect of errors.
                try:
                    if (len(myData[0]) == len(myData[i+1])):
                        print("Printing %d: \tDimensions %d \tx\t %d" % (i+1, len(myData[0]), len(myData[i+1])))  
                        graph.plot(myData[0][-sampleSize:], myData[i+1][-sampleSize:], clear = False,pen=(i,numberOfElements), name = "C " + str(i + 1))
                    else:
                        print("Data length incorrect")
                except:
                    e = sys.exc_info()
                    print("Error during plotting")
                    print(e)
                    pgmExit = True
        elif dataMode == 1:
            for i in range(numberOfElements-1):   
                # this is often the suspect of errors.
                try:
                    if (len(myData[1]) == len(myData[i+2])):
                        # print("Printing %d: \tDimensions %d \tx\t %d" % (i+1, len(myData[1]), len(myData[i+2])))  
                        graph.plot(myData[1][-sampleSize:], myData[i+2][-sampleSize:], clear = False,pen=(i,numberOfElements), name = "C " + str(i + 1))
                    else:
                        print("Data length incorrect")
                except:
                    e = sys.exc_info()
                    print("Error during plotting")
                    print(e)
                    pgmExit = True

        dataReady = False
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):            
        QtGui.QApplication.processEvents()


if __name__=='__main__':   
    print("attempting connection to %s at baud %d" % (port, baud))    
    try:
        # connect to serial port
        serial_port = serial.Serial(port, baud, timeout=1)
        print('Connected')
    except:
        e = sys.exc_info()
        serial_port = None
        print("Error connecting to serial")
        print(e)
        # time.sleep(5) # delays for 5 seconds
        serial_port.close()
        serial_port = None
        serial_port.exit()

    if serial_port != None:
        print("Starting serial thread")
        # begin serial parsing thread
        serialThread = threading.Thread(target=serialParser, args=(serial_port,))
        serialThread.setDaemon(True)  # set as daemon so when main thread exits it also exits
        serialThread.start()

        while initialised == False:
            pass
        
        print("Press any key to exit")


        # QtGui.QApplication.exec_()

        while True:
            updatePlot()
            if msvcrt.kbhit():
                # key = msvcrt.getch()
                break
            if pgmExit == True:
                print("Exiting as called by thread")
                break

        serial_port.close()
        serial_port = None
        serialThread.stop
        sys.exit()