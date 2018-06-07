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

        camProxy = ALProxy("ALVideoDevice", naoIP, naoPort)
        resolution = 2    # VGA
        colorSpace = 11   # RGB

        addr = (procIP, procPort)
        skipframe = 2

        counter = 0

        while(True):

            videoClient = camProxy.subscribe(str(random.randint(0,10000)), resolution, colorSpace, 5)
            naoImage = camProxy.getImageRemote(videoClient)
            imageWidth = naoImage[0]
            imageHeight = naoImage[1]
            array = naoImage[6]

            # create a cv2 image
            temp = np.frombuffer(array, dtype=np.uint8).reshape(imageHeight,imageWidth,3)
            frame = temp.copy()
            frame[:,:,0],frame[:,:,2] = temp[:,:,2],temp[:,:,0]

            # write object to file
            cv2.imwrite("streamImg.jpg",frame)
            
            cv2.imshow('frameNao',frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                exit(0)

            camProxy.unsubscribe(videoClient)


            if(counter % skipframe == 0):
            # for testing, use webcam feed
            # send every third frame
            # ensures that prev frame is read by receiver
            s = socket(AF_INET, SOCK_DGRAM)
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


if __name__ == '__main__':
    main()
