# Smart cities: A case study in waste monitoring and management
#### A skeleton for developing a smart trash collection &amp; bin management system

### Notice: All passwords (Databases, sensors, etc.) have to be changed in order to get it to work. The mentioned ones are not online anymore

# General

Code and results of a two week trash collection pilot test at the Technical University of Denmark. Made by André Castro Lundin
Supervisor: Ali Gurcan Ozkil

# Contents

## Sensors
(only software in this repository)

## Gateway
(only software in this repository)

## Network setup
https://github.com/ttn-zh/ic880a-gateway/tree/spi 

## Backend

* Built in Node-RED as it allowed to work in a lean matter for quick prototyping and reprototyping
* Communication from The Things network was MQTT (though started as HTTP which is still implemented in the code)
* Cloudant NoSQL database used thanks to its flexibility for changes throughout the project

## Frontend
* Built on Python Flask

## Data analysis
* Using Jupyter notebook

## All data
* The raw data
* The processed data
* For the images and videos, contact me
