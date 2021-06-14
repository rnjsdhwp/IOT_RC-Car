import paho.mqtt.client as mqtt
import time
from gpiozero import LED, Buzzer, DistanceSensor, Robot
from time import sleep
import cv2
import os
import numpy as np
import RPi.GPIO as gpio

ip_address = '192.168.227.122'
active=0
client = mqtt.Client()
robot=Robot(left=(27,22), right=(15,14))
led_right=LED(20)
led_left=LED(16)
buzzer=Buzzer(21)
#distance_sensor = DistanceSensor(echo=24, trigger=23)
gpio.setmode(gpio.BCM)
trig = 23
echo = 24
gpio.setup(trig, gpio.OUT)
gpio.setup(echo, gpio.IN)

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

#서버로부터 publish message를 받을 때 호출되는 콜백
def on_subscribe(client, userdata, mid, granted_qos):
    print("subscribed: " + str(mid) + " " + str(granted_qos))

def on_message(client, userdata, msg):
    print(str(msg.payload.decode("utf-8")))
    global active
    if(str(msg.payload.decode("utf-8"))=="1"):
        gpio.output(trig, False)
        time.sleep(0.5)
        gpio.output(trig, True)
        time.sleep(0.00001)
        gpio.output(trig, False)
        while gpio.input(echo) == 0 :
            pulse_start = time.time()
        while gpio.input(echo) == 1 :
            pulse_end = time.time()

        pulse_duration = pulse_end - pulse_start
        distance = pulse_duration * 17000
        distance = round(distance, 2)
        if((active == 0) and (distance>20)):
            robot.forward(0.2)
            time.sleep(0.5)
            robot.stop()
    elif(str(msg.payload.decode("utf-8"))=="2"):
        if(active == 1):
            robot.left(0.2)
            time.sleep(1)
            robot.stop()
    elif(str(msg.payload.decode("utf-8"))=="3"):
        if(active == 1):
            led_right.on()
            led_left.on()
            robot.backward(0.2)
            time.sleep(1)
            robot.stop()
            led_right.off()
            led_left.off()
    elif(str(msg.payload.decode("utf-8"))=="4"):
        if(active == 1):
            robot.right(0.2)
            time.sleep(1)
            robot.stop()
    elif(str(msg.payload.decode("utf-8"))=="5"):
        if(active == 1):
            buzzer.beep(0.1)
    elif(str(msg.payload.decode("utf-8")) == "0"):
        detection()

#def buzzer_sound():
    

def detection():
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read('train/trainer.yml')
    cascadePath = "haarcascades/haarcascade_frontalface_default.xml"
    faceCascade = cv2.CascadeClassifier(cascadePath);
    font = cv2.FONT_HERSHEY_SIMPLEX

    #iniciate id counter
    id = 0

    # names related to ids: example ==> loze: id=1,  etc
    # 이런식으로 사용자의 이름을 사용자 수만큼 추가해준다.
    names = ['oje', 'Kwon']

    # Initialize and start realtime video capture
    cam = cv2.VideoCapture(0)
    cam.set(3, 640) # set video widht
    cam.set(4, 480) # set video height
# Define min window size to be reognized as a face
    minW = 0.1*cam.get(3)
    minH = 0.1*cam.get(4)

    while True:
        ret, img =cam.read()
        #img = cv2.flip(img, -1) # Flip vertically
        gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

        faces = faceCascade.detectMultiScale(gray,scaleFactor = 1.2,minNeighbors = 5,minSize = (int(minW), int(minH)),)

        for(x,y,w,h) in faces:
            cv2.rectangle(img, (x,y), (x+w,y+h), (0,255,0), 2)
            id, confidence = recognizer.predict(gray[y:y+h,x:x+w])
            # Check if confidence is less them 100 ==> "0" is perfect match
            if (confidence < 100):
                id = names[id]
                confidence = "  {0}%".format(round(100 - confidence))
            else:
                id = "unknown"
                confidence = "  {0}%".format(round(100 - confidence))

            cv2.putText(img, str(id), (x+5,y-5), font, 1, (255,255,255), 2)
            cv2.putText(img, str(confidence), (x+5,y+h-5), font, 1, (255,255,0), 1)

        cv2.imshow('camera',img)
        k = cv2.waitKey(10) & 0xff # Press 'ESC' for exiting video
        if k==27:
            break
        if(id == "Kwon"):
            global active
            active=1
            break
    # Do a bit of cleanup
    print("\n [INFO] Exiting Program and cleanup stuff")
    cam.release()
    cv2.destroyAllWindows()



client.on_connect = on_connect #콜백설정
client.on_subscribe = on_subscribe
client.on_message = on_message #콜백설정

client.connect(ip_address, 1883)  # 라즈베리파이 커넥트
client.subscribe('hello/world', 0)  # 토픽 : temp/temp  | qos : 1

client.loop_forever()
