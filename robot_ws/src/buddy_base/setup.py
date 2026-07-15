from setuptools import setup

package_name = "buddy_base"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages",
         ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools", "pyserial"],
    zip_safe=True,
    description="Buddy base bridge: /cmd_vel <-> drive MCU protocol <-> /odom.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "bridge_node = buddy_base.ros_bridge_node:main",
        ],
    },
)
