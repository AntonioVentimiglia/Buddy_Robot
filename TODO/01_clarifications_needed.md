# Clarifications Needed from You

These are the information gaps needed to turn this scaffold into a concrete design. You do **not** need to answer them all before using the repository, but they should be answered before buying major hardware.

## Mission and environment

1. Indoor only, outdoor only, or mixed? - Indoor.
2. Surface types: smooth floor, carpet, tile transitions, sidewalk, grass, gravel, ramps? - Carpet and marble.
3. Minimum doorway/hallway width? - 0.75m, aiming for 0.3 m x 0.3 m footprint.
4. Will it operate near people, children, pets, fragile furniture, or public spaces? - Yes.
5. Is the first robot for learning, research, practical tasks, demonstrations, or eventual productization? - Learning and practical tasks.

## Mobility

6. Target top speed and normal cruise speed. - 2.5 m/s and 1.5 m/s.
7. Desired acceleration and stopping distance. - no desired acceleration, 0.25 m stopping distance.
8. Maximum ramp angle or threshold height. - 20 deg and none
9. Preferred robot footprint limits: length, width, height. - 0.3 m x 0.3 m x whatever
10. Desired ground clearance. - enought to get over changes in surfaces. 0.05m
11. Is four-wheel differential intended to be skid-steer with four driven wheels, or two driven wheels plus passive support? Current assumption: four driven wheels. Not group, each side has its own motor.

## Payload and manipulation

12. Estimated total robot mass target. - 20 kg
13. Payload to carry on the base. - 10 kg
14. Whether an arm is required for v1. - No
15. If arm is required: payload, reach, precision, degrees of freedom, gripper type, and budget. - TBD
16. Any tasks the arm must perform: pick up objects, press buttons, open doors, carry tools, interact with shelves? - All of the mentioned. 

## Sensors

17. LiDAR range requirement and field of view requirement. - TBD
18. Indoor lighting/outdoor sunlight constraints for RGB-D camera. - Will need to operate with indoor lighting 
19. Required camera depth range. - TBD
20. Need for object detection, people detection, fiducials, grasping, teleop video, or mapping? - Needs to observe objects to avoid of interact with. 
21. Is a 3D LiDAR/depth obstacle layer likely later? - Unknown, will need to see its funcitionality. 

## Power

22. Runtime target in minutes/hours. - 60 min
23. Battery preference: Li-ion, LiFePO4, swappable packs, charging dock. - Most energy dense
24. Acceptable battery weight. -  Lighest it can be but not too expensive. 
25. Whether robot must charge autonomously. - Yes
26. Expected max power for arm if added. - TBD

## Compute and development

27. Exact Jetson Orin Nano Super storage plan: SD card only or NVMe boot/storage? - probably SD card
28. Development host: Mac, Windows, Linux, or mixed? - Mac and Windows
29. Do you want Docker on-robot, native ROS install, or both? - Whatever is necessary
30. Do you want cloud/private remote access, or local network only? - Both? 

## Embedded control

31. Preferred MCU ecosystem: STM32, Teensy, ESP32, RP2040/RP2350, Arduino-class, other. - Don't know, whatever is appropriate
32. Preferred bus: CAN/CAN-FD, RS485, USB serial, Ethernet, micro-ROS. - Whatever is necessary
33. Comfort level with C/C++, PlatformIO, STM32Cube, FreeRTOS, Zephyr, or Arduino. - I will learn whatever I need
34. Need OTA flashing to MCUs from the Jetson, or is wired flashing acceptable during v1? Preferably OTA

## Budget and procurement

35. Total budget range for v1. - 300-600 USD
36. Budget range for motors/drivers. - TBD
37. Budget range for LiDAR/camera. - TBD
38. Budget range for arm if included. - TBD
39. Preference for hobby parts, industrial components, or a middle path. - Cheaper, I can make stuff myself if needed. 

## Safety and operations

40. Who is allowed to operate it? - Anyone with the proper 
41. Is remote operation allowed when no one is physically near E-stop? - Yes
42. Required E-stop quantity and placement. - TBD
43. Maximum allowed autonomous speed around people. - TBD
44. Any local standards, school/lab rules, or insurance constraints? - None
