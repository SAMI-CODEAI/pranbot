This Markdown (MD) document outlines the complete wiring and pin configuration for your ESP32 Gas Robot, based on the provided source code.

---

# 🤖 Gas Robot Connection Guide

This document provides the hardware mapping for the **Gas_Robot_AP** system. It uses an **ESP32** to monitor air quality and provide autonomous obstacle avoidance.

## 🔌 1. Power Distribution

| Component | Connection | Notes |
| --- | --- | --- |
| **ESP32 VIN** | Battery (+) | Use a voltage regulator if battery > 5V. |
| **L298N VCC** | Battery (+) | Direct battery power (e.g., 7.4V or 12V). |
| **Common GND** | Battery (-) | <br>**Crucial:** Connect ESP32 GND and L298N GND.

 |
| **MQ Sensors VCC** | ESP32 5V / External 5V | MQ sensors require 5V to heat the element. |

---

## 🏎️ 2. Motor Controller (L298N)

The motors are controlled using PWM on channels 0 and 1.

| ESP32 Pin | L298N Pin | Function |
| --- | --- | --- |
| **GPIO 12** | **ENA** | Speed Control Motor A (PWM) 

 |
| **GPIO 13** | **ENB** | Speed Control Motor B (PWM) 

 |
| **GPIO 25** | **IN1** | Motor A Direction 1 

 |
| **GPIO 26** | **IN2** | Motor A Direction 2 

 |
| **GPIO 27** | **IN3** | Motor B Direction 1 

 |
| **GPIO 14** | **IN4** | Motor B Direction 2 

 |

---

## ⚠️ 3. Gas & Safety Sensors

These sensors use Analog inputs to detect hazardous conditions.

| ESP32 Pin | Sensor Model | Detected Gas | Emergency Threshold |
| --- | --- | --- | --- |
| **GPIO 34** | **MQ-2** | Smoke / Combustion | <br>`> 2000` (Stop) 

 |
| **GPIO 35** | **MQ-3** | Methane | N/A 

 |
| **GPIO 32** | **MQ-7** | Carbon Monoxide (CO) | <br>`> 1500` (Stop) 

 |
| **GPIO 33** | **MQ-135** | Air Quality | N/A 

 |
| **GPIO 36** | **BAT** | Battery Level | Monitoring via API 

 |

---

## 🛡️ 4. Obstacle Avoidance (IR)

Digital infrared sensors used for the autonomous logic loop.

| ESP32 Pin | Sensor Position | Logic |
| --- | --- | --- |
| **GPIO 4** | **Left IR** | <br>`LOW` = Obstacle detected 

 |
| **GPIO 5** | **Right IR** | <br>`LOW` = Obstacle detected 

 |

---

## 🌐 5. Network & API Info

* 
**SSID:** `Gas_Robot_AP` 


* 
**Password:** `12345678` 


* 
**Data Endpoint:** `/data` (Returns JSON of all sensor values) 


* 
**Control Endpoint:** `/cmd?d=` (f=forward, b=back, l=left, r=right, s=stop) 


* 
**Auto Toggle:** `/auto?v=1` (Enable) or `v=0` (Disable) 



---
