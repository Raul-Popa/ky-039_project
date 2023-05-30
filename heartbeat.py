import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import RPi.GPIO as GPIO

LED_MONITOR_PIN = 6
LED_PINS = [16, 12, 13, 5, 25]


GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_MONITOR_PIN,GPIO.OUT)

for PIN in LED_PINS:
    GPIO.setup(PIN,GPIO.OUT)

def updateLeds(arr):
    for i in range(len(arr)):
        GPIO.output(LED_PINS[i],  GPIO.HIGH if arr[i] == 1 else GPIO.LOW)


i2c = busio.I2C(board.SCL, board.SDA)

ads = ADS.ADS1115(i2c)


chan0 = AnalogIn(ads, ADS.P0)
chan1 = AnalogIn(ads, ADS.P1)
chan2 = AnalogIn(ads, ADS.P2)
chan3 = AnalogIn(ads, ADS.P3)

if __name__ == '__main__':
    
    GAIN = 2/3
    curState = 0
    thresh = 525 
    Peak = 512
    Trough = 512
    stateChanged = 0
    sampleCounter = 0
    lastBeatTime = 0
    firstBeat = True
    secondBeat = False
    Pulse = False
    IBI = 60
    rate = [0]*10
    amp = 100
    lastTime = int(time.time()*1000)
    prevValues = [-1, -1, -1, -1, -1]
    
    while True:
        BPM = 0
        
        Signal = chan0.value 
        curTime = int(time.time()*1000)
        sampleCounter += curTime - lastTime
        lastTime = curTime
        N = sampleCounter - lastBeatTime
        
        if Signal < thresh and N > (IBI/5.0)*3.0 :
            if Signal < Trough : 
                Trough = Signal
        if Signal > thresh and Signal > Peak: 
            Peak = Signal
        
        if N > 250 :
            if (Signal > thresh) and (Pulse == False) and (N > (IBI/5.0)*3.0) :
                GPIO.output(LED_MONITOR_PIN, GPIO.HIGH)
                Pulse = True
                IBI = sampleCounter - lastBeatTime
                lastBeatTime = sampleCounter
                if secondBeat :
                    secondBeat = False
                    for i in range(0,10):
                        rate[i] = IBI
                if firstBeat :
                    firstBeat = False
                    secondBeat = True
                    continue                
                
                runningTotal = 0
                for i in range(0,9):
                    rate[i] = rate[i+1]
                    runningTotal += rate[i]
                rate[9] = IBI
                runningTotal += rate[9]
                runningTotal /= 10
                BPM = 60000/runningTotal
                print ('BPM: {}'.format(BPM))
        if Signal < thresh and Pulse == True :
            GPIO.output(LED_MONITOR_PIN, GPIO.LOW)
            Pulse = False
            amp = Peak - Trough
            thresh = amp/2 + Trough
            Peak = thresh
            Trough = thresh
        if N > 2500 :
            thresh = 512
            Peak = 512
            Trough = 512
            lastBeatTime = sampleCounter
            firstBeat = True
            secondBeat = False
            GPIO.output(LED_MONITOR_PIN, GPIO.LOW)
            print ("no beats found")
        
        if(BPM < 50):
            values = [0, 0, 0, 0, 0]
        elif(BPM < 70):
            values = [1, 0, 0, 0, 0]
        elif(BPM < 90):
            values = [1, 1, 0, 0, 0]
        elif(BPM < 110):
            values = [1, 1, 1, 0, 0]
        elif(BPM < 130):
            values = [1, 1, 1, 1, 0]
        else:
            values = [1, 1, 1, 1, 1]


        if(prevValues != values):
            updateLeds(values)

        prevValues = values

        time.sleep(0.05)
