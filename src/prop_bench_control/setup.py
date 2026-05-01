from setuptools import setup, find_packages
import os
from glob import glob

package_name = 'prop_bench_control'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.py')),
        # Throttle profiles are resolved at runtime by main._find_throttle_profile_dir()
        # which walks up the repo tree — no install step needed.
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Pravin Wedage',
    maintainer_email='pravin.wedage@flight.utias.utoronto.ca',
    description='ROS2 offboard throttle controller for Pixhawk 6 prop bench',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'prop_bench_gui = prop_bench_control.main:main',
        ],
    },
)
