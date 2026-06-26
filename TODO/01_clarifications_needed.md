# Clarifications Needed from You

These are the information gaps needed to turn this scaffold into a concrete design. You do **not** need to answer them all before using the repository, but they should be answered before buying major hardware.

## Mission and environment

1. Indoor only, outdoor only, or mixed?
2. Surface types: smooth floor, carpet, tile transitions, sidewalk, grass, gravel, ramps?
3. Minimum doorway/hallway width?
4. Will it operate near people, children, pets, fragile furniture, or public spaces?
5. Is the first robot for learning, research, practical tasks, demonstrations, or eventual productization?

## Mobility

6. Target top speed and normal cruise speed.
7. Desired acceleration and stopping distance.
8. Maximum ramp angle or threshold height.
9. Preferred robot footprint limits: length, width, height.
10. Desired ground clearance.
11. Is four-wheel differential intended to be skid-steer with four driven wheels, or two driven wheels plus passive support? Current assumption: four driven wheels grouped left/right.

## Payload and manipulation

12. Estimated total robot mass target.
13. Payload to carry on the base.
14. Whether an arm is required for v1.
15. If arm is required: payload, reach, precision, degrees of freedom, gripper type, and budget.
16. Any tasks the arm must perform: pick up objects, press buttons, open doors, carry tools, interact with shelves?

## Sensors

17. LiDAR range requirement and field of view requirement.
18. Indoor lighting/outdoor sunlight constraints for RGB-D camera.
19. Required camera depth range.
20. Need for object detection, people detection, fiducials, grasping, teleop video, or mapping?
21. Is a 3D LiDAR/depth obstacle layer likely later?

## Power

22. Runtime target in minutes/hours.
23. Battery preference: Li-ion, LiFePO4, swappable packs, charging dock.
24. Acceptable battery weight.
25. Whether robot must charge autonomously.
26. Expected max power for arm if added.

## Compute and development

27. Exact Jetson Orin Nano Super storage plan: SD card only or NVMe boot/storage?
28. Development host: Mac, Windows, Linux, or mixed?
29. Do you want Docker on-robot, native ROS install, or both?
30. Do you want cloud/private remote access, or local network only?

## Embedded control

31. Preferred MCU ecosystem: STM32, Teensy, ESP32, RP2040/RP2350, Arduino-class, other.
32. Preferred bus: CAN/CAN-FD, RS485, USB serial, Ethernet, micro-ROS.
33. Comfort level with C/C++, PlatformIO, STM32Cube, FreeRTOS, Zephyr, or Arduino.
34. Need OTA flashing to MCUs from the Jetson, or is wired flashing acceptable during v1?

## Budget and procurement

35. Total budget range for v1.
36. Budget range for motors/drivers.
37. Budget range for LiDAR/camera.
38. Budget range for arm if included.
39. Preference for hobby parts, industrial components, or a middle path.

## Safety and operations

40. Who is allowed to operate it?
41. Is remote operation allowed when no one is physically near E-stop?
42. Required E-stop quantity and placement.
43. Maximum allowed autonomous speed around people.
44. Any local standards, school/lab rules, or insurance constraints?
