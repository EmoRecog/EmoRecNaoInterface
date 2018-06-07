import pickle
import Queue
from socket import *
import struct
import sys
import threading

import cv2
import numpy as np

import argparse

from naoqi import ALProxy
import random

class FrameRetriever(threading.Thread):
    
    def __init__(self, naoIP, naoPort, frameQueue):
        '''
        should retrieve frames from the bot
        put them on a queue
        '''
        threading.Thread.__init__(self)
        self.naoIP = naoIP
        self.naoPort = naoPort
        self.frameQueue = frameQueue

    def run(self):
        try:
            camProxy = ALProxy("ALVideoDevice", self.naoIP, self.naoPort)
            resolution = 2    # VGA
            colorSpace = 11   # RGB

            while(True):

                videoClient = camProxy.subscribe(str(random.randint(0,10000)), resolution, colorSpace, 5)
                naoImage = camProxy.getImageRemote(videoClient)
                imageWidth = naoImage[0]
                imageHeight = naoImage[1]
                array = naoImage[6]
                '''
                Image container is an array as follow:
                [0]: width.
                [1]: height.
                [2]: number of layers.
                [3]: ColorSpace.
                [4]: time stamp (seconds).
                [5]: time stamp (micro-seconds).
                [6]: binary array of size height * width * nblayers containing image data.
                [7]: camera ID (kTop=0, kBottom=1).
                [8]: left angle (radian).
                [9]: topAngle (radian).
                [10]: rightAngle (radian).
                [11]: bottomAngle (radian).
                '''

                # create a cv2 image
                temp = np.frombuffer(array, dtype=np.uint8).reshape(imageHeight,imageWidth,3)
                frame = temp.copy()
                frame[:,:,0],frame[:,:,2] = temp[:,:,2],temp[:,:,0]

                # write object to Queue
                self.frameQueue.put_nowait(frame)
                
                cv2.imshow('frame',frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    exit(0)

                camProxy.unsubscribe(videoClient)

        except KeyboardInterrupt:
            # kill with Ctrl + c
            print("NAO video stream closed")

class FrameDispatcher(threading.Thread):
    def __init__(self, procIP, procPort, frameQueue):
    # def __init__(self, procIP, procPort):

        '''
        should read frames from queue
        send them to the processing server
        '''
        threading.Thread.__init__(self)
        self.procIP = procIP
        self.procPort = procPort
        self.frameQueue = frameQueue

    def run(self):
        
        # testing
        # cap = cv2.VideoCapture(2)
              
        addr = (self.procIP, self.procPort)
        skipframe = 1

        counter = 0
        while True:
            try:           
                # test, remote the try/except block for Queue.Empty for testing
                # ret, frame = cap.read()
                
                frame = self.frameQueue.get()
                
                if(counter % skipframe == 0):
                    # for testing, use webcam feed
                    # send every third frame
                    # ensures that prev frame is read by receiver
                    s = socket(AF_INET, SOCK_DGRAM)
                    cv2.imwrite("streamImg.jpg",frame)
                    f = open("streamImg.jpg", "rb")
                    data = f.read(1024)
                    while data:
                        if(s.sendto(data, addr)):
                            data = f.read(1024)
                    f.close()
                    s.close()
                    
                cv2.imshow('sender',frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                counter += 1


            except Queue.Empty:
                pass     
       
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--nIP", help="nao IP")
    parser.add_argument("--nP", help="nao Port")
    parser.add_argument("--IP", help="proc IP")
    parser.add_argument("--P", help="proc Port")

    if(len(sys.argv)<2):
        parser.print_usage()
        sys.exit(1)

    args = parser.parse_args()

    if(args.nIP and
        args.nP and
        args.IP and
        args.P):
        
        naoIP = args.nIP
        naoPort = args.nP
        # naoIP = '172.16.138.31'
        # naoPort = 9559

        procIP = args.IP
        procPort = args.P
        # procIP = '127.0.0.1'
        # procPort = 4096

        frameQueue = Queue.Queue()

        try:
            frameRetriever = FrameRetriever(naoIP, naoPort, frameQueue)
            frameDispatcher = FrameDispatcher(procIP, procPort, frameQueue)

            frameRetriever.start()
            frameDispatcher.start()
        except KeyboardInterrupt:
            exit(1)
        

    

if __name__ == '__main__':
    main()
