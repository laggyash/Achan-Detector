<img width="3188" height="1202" alt="frame (3)" src="https://github.com/user-attachments/assets/517ad8e9-ad22-457d-9538-a9e62d137cd7" />


# അച്ഛൻ-Detector 🧍🏻‍♂️


## Basic Details
### Team Name: 113


### Team Members
- Team Lead: Aswin G Ajay - MITS
- Member 2: Fahim Faisel - MITS

### Project Description
This project uses the home CCTV camera streams to analyze when a specific person exits the house and leaves in a motor vehicle, and sends a notification to the user's phone

### The Problem (that doesn't exist)
The problems can be divided into two very different sections:
i) Whenever I'm travelling home for the weekend and I get off the bus, I'm left waiting wondering when my dad is gonna come pick me up or whether he has left home at all. This often results in multiple phone calls to my mom, to check whether my dad's on the way.
ii) It is very common for me to hangout with my friends, lose track of time and come home later than expected. Getting in without facing the wrath of my dad is an issue I always face.

### The Solution (that nobody asked for)
The solution? അച്ഛൻ-Detector uses my trusty old Raspberry Pi and my home CCTV camera feed to recognize when my dad leaves the house or is on his way to pick me up, and gives me an estimate of when he'll reach me!

## Technical Details
### Technologies/Components Used
For Software:
- [Python, HTML, CSS, JavaScript]
- [FastAPI (for the backend API)]
- [Python: requests (for making API calls), ultralytics (for YOLO object detection), opencv-python (for video processing), python-dotenv (for managing environment variables)
JavaScript: Tone.js (for sound effects)]
- [YOLOv8n (pre-trained object detection model), Google Maps Directions API]

For Hardware:
- [ A camera (like a webcam or security camera) capable of providing a video feed.]

### Implementation
For Software:
# Installation
[pip install fastapi uvicorn python-dotenv requests opencv-python ultralytics]

# Run
[uvicorn main:app --reload]

### Project Documentation
For Software:

# Screenshots (Add at least 3)
[https://drive.google.com/file/d/1wZTCuwF2tHw-v_BPIhlayHKbajRrAhSg/view?usp=sharing]
*front end - website front showing live feed video(static vid for now)

[https://drive.google.com/file/d/1aaSeX_i9NRuArxpYxM5V5TT7CYKSTIM5/view?usp=sharing]
*API will fetch the data from google maps and display in the extended window

[https://drive.google.com/file/d/1HtquE4WrjJi6jLRDnwAT3AuOzSZ03GRO/view?usp=sharing]
*shows the estimates and data fetched from the api 


# Diagrams
![Nil]

# Schematic & Circuit
![Nil]

# Build Photos
![Nil]

### Project Demo
# Video
[https://drive.google.com/file/d/1eJ5jqnm97wSGagdOv2uLgBcjTDCNPh1m/view?usp=sharing]
*As soon as the father leaves home in his car, a notification is triggered, providing his estimated time of arrival and departure timestamp.*

# Additional Demos
[NIL]

## Team Contributions
- [Aswin G Ajay]: [Full backend development, including the object detection logic with YOLOv8 and video processing.]
- [Fahim Faisel]: [ API creation with FastAPI and all frontend development, including the HTML, CSS, and dynamic JavaScript functionality.]


---
Made with ❤️ at TinkerHub Useless Projects 

![Static Badge](https://img.shields.io/badge/TinkerHub-24?color=%23000000&link=https%3A%2F%2Fwww.tinkerhub.org%2F)
![Static Badge](https://img.shields.io/badge/UselessProjects--25-25?link=https%3A%2F%2Fwww.tinkerhub.org%2Fevents%2FQ2Q1TQKX6Q%2FUseless%2520Projects)


