import paho.mqtt.client as mqtt
import time, cv2, os, datetime
from gpiozero import LED, Buzzer, DistanceSensor, Robot
from time import sleep
import numpy as np
#import RPi.GPIO as gpio

ip_address = '192.168.143.47'
active=0
client = mqtt.Client()
robot=Robot(left=(27,22), right=(15,14))
led_right=LED(20)
led_left=LED(16)
buzzer=Buzzer(21)
distance = DistanceSensor(echo=24, trigger=23)
"""
gpio.setmode(gpio.BCM)
trig = 23
echo = 24
gpio.setup(trig, gpio.OUT)
gpio.setup(echo, gpio.IN)
"""

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

#서버로부터 publish message를 받을 때 호출되는 콜백
def on_subscribe(client, userdata, mid, granted_qos):
    print("subscribed: " + str(mid) + " " + str(granted_qos))

def on_message(client, userdata, msg):
	print(str(msg.payload.decode("utf-8")))
	global active
	#정지
	if(str(msg.payload.decode("utf-8")) == "stop"):
		if(active == 1):
			robot.stop()
			led_right.off()
			led_left.off()
			buzzer.off()
	#전진,천천히 멈추게
	elif(str(msg.payload.decode("utf-8"))=="1"):
		#토글로 누르면 저진하다가 떼면 다른숫자로 sopt?
		print(distance)
		if(distance.distance*100 > 25):
			if(active == 1):
				print("Robot Forward")
				robot.forward(0.2)
		else:
			print("robot stop")
			robot.stop()
	#좌회전
	elif(str(msg.payload.decode("utf-8"))=="2"):
		if(active == 1):
			led_left.on()
			robot.left(0.2)
	#후진, 소리가 울리다가 토글버튼 손떼면 스탑
	elif(str(msg.payload.decode("utf-8"))=="3"):
		if(active == 1):
			led_right.on()
			led_left.on()
			buzzer.beep(1,1,100)
			robot.backward(0.2)
	#우회전
	elif(str(msg.payload.decode("utf-8"))=="4"):
		if(active == 1):
			led_right.on()
			robot.right(0.2)
	#부저, 어플버튼 토글해ㅓ서 손뗴면 stop보내게하기
	elif(str(msg.payload.decode("utf-8"))=="5"):
		if(active == 1):
			buzzer.on()
			#time.sleep(0.5)
			#buzzer.beep(1)
			#buzzer.off()
	#얼굴인식
	elif(str(msg.payload.decode("utf-8")) == "0"):
		detection()

def detection():
	recognizer = cv2.face.LBPHFaceRecognizer_create()
	recognizer.read('train/trainer.yml')
	cascadePath = "haarcascades/haarcascade_frontalface_default.xml"
	faceCascade = cv2.CascadeClassifier(cascadePath);
	font = cv2.FONT_HERSHEY_SIMPLEX

	#iniciate id counter
	id = 0

	# names related to ids: example ==> Kwon: id=1
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
			client.publish("hello/world", "OK")
			break
	# Do a bit of cleanup
	print("\n [INFO] Exiting Program and cleanup stuff")
	cam.release()
	cv2.destroyAllWindows()

client.on_connect = on_connect #콜백설정
client.on_subscribe = on_subscribe
client.on_message = on_message #콜백설정

client.connect(ip_address, 1883)  # 라즈베리파이 커넥트
client.subscribe('hello/world', 0)  # 토픽 : hello/world, qos : 0

client.loop_forever()
