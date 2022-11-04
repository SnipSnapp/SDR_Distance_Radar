import math
import argparse
import time
import pyautogui
import numpy
import os
from matplotlib import pyplot
from rtlsdr import *
import webbrowser
import folium



#gets wattage power from dbm, an unnecessary step and I'm not changing it now.
def get_watts(dbm):
    return (10 ** (dbm/ 10))/1000
#return distance from a src using inverse square law
def get_dist(I1, I2,d1):
    return math.sqrt((I1/I2)*(d1**2))
#args
def set_vars():
    parser = argparse.ArgumentParser()
    parser.add_argument("-Tx","--Transmission_Frequency",type=float,help="The transmission frequency(MHz) of your target. (default"
                                                              ":46.515)", default=46.515)
    parser.add_argument("-w", "--Wattage",type=int, help= "The transmission wattage the target frequency is transmitting at. (de"
                                                 "faults:40). Reference: https://wireless2.fcc.gov/UlsApp/UlsSearch/sea"
                                                 "rchLicense.jsp; ", default=40)
    parser.add_argument("-lat","--Latitude", type=float,help="Your Latitude.(default:40)", default=40)
    parser.add_argument("-lon","--Longitude", type=float,help="Your Longitude (default:40)", default=40)
    parser.add_argument("-u","--Update_time", type=int, help="The time between map updates in seconds. (default:10)", default=10)
    #parser.add_argument("-sr", "--Sample_Rate", help="The sample rate of your SDR. (default:auto)", default=None)
    parser.add_argument("-g", "--Gain",type=float, help="SDR Gain. (Automatic if no option provided)", default=None)
    parser.add_argument("-Txd1", "--Transmission_RP_Distance", type=float,help="Tx reference-point distance, This is how far away you a"
                                                               "re on the first received transmission. This is a const"
                                                               "ant in meters >1. (default:1)", default=1)

    return parser.parse_args()

if __name__ == '__main__':
    args = set_vars()
    coordinates=[args.Latitude, args.Longitude]
    mapObj=folium.Map(location=coordinates, zoom_start=20)
    mapObj.save('output.html')
    #init_sdr
    sdr = RtlSdr()
    tx_pow = args.Wattage
    sdr.center_freq = args.Transmission_Frequency*1e7
    center_freq_cmp_val=numpy.float64(sdr.center_freq / 1e6)
    if args.Gain is None:
        sdr.gain= 'auto'
    else:
        sdr.gain=args.Gain
    print("Listening on: " + str(center_freq_cmp_val))
    max = 10.2
    dist = 2.8
    #check for output file existing.
    if os.path.exists(os.path.realpath("output.html")):
        webbrowser.open('file://' + os.path.realpath("output.html"), new=0)
    else:
        with open('output.html', 'w') as f:
            f.write('Building map...')
            f.close()
        webbrowser.open('file://' + os.path.realpath("output.html"), new=0)
    #read from SDR.
    while True:
        for z in range(100):
            samples = sdr.read_samples(1024)
            ok = pyplot.psd(samples, NFFT=1024, Fs=sdr.sample_rate / 1e6, Fc=sdr.center_freq / 1e6)
            pyplot.xlabel('Frequency (MHz)')
            pyplot.ylabel('Relative power (dB)')
            for y,x in enumerate(ok[1]):

                if abs(ok[1][y] - center_freq_cmp_val) < 1e-9:
                    rx_watts = get_watts(ok[0][y])
                    dist = get_dist(tx_pow,rx_watts,1)
                    if int(float(dist)) > int(float(max)):
                        max = float(dist)
                        print("rcv dbm: "+str(ok[0][y]) )
                        print("rcv wat: "+str(rx_watts))
                        print("clc dist: "+ str(dist) + "m" )

        #Ensure you have some kind of actionable data. 
        if max > 20:
            folium.Circle(radius=max, location=coordinates).add_to(mapObj)
            os.remove(os.path.realpath('output.html'))
            mapObj.save('output.html')
            pyautogui.hotkey('f5')
        time.sleep(args.Update_time)


