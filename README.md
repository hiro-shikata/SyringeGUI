# SyringeGUI
Python-based GUI to control stepping motor-controlled syringe pumps.

This project provide you with the tools to control DIY syringe pumps (max. 3 pumps) connected to Ardiuno device.


## Hardware requirements

- DIY syringe pumps consisted of stepping motors and an actuator such as lead screws and slider. 
- As control devices, 1x Arduino Uno/Nano and stepping motor drivers (as many as needed) like DRV8825, A4988, etc.
- Option: CNC shield v3.0 for Arduino Uno or CNC shield v4.0 forr Arduino Nano
  * You can use only highest microstepping of the stepper driver with CNC shield v4.0 if the board is not modified.
- Any computers that can run Python 3.10 or higher (Mac, Win, Linux, or Raspberry Pi )

You can find many good instructions on making DIY syringe pumps. I was really impressed and inspired by the "poseidon" system to start this project.

https://github.com/pachterlab/poseidon

https://www.instructables.com/DIY-Syringe-Pump/

https://chem.uncg.edu/croatt/flow-chemistry/building-the-syringe-pump/

https://reprap.org/wiki/Open-source_syringe_pump

https://www.mass-spec.ru/projects/diy/syringe_pump/eng/


Note: In this project, syringe pumps were bought from a chinese company.


## Software Installation Guide

This project consists of two main tools:

	SyringeGUI: The main controller for the syringe pumps.

	Config Generator: A utility to create and manage config.json for different mechanical setups and syringe types.

Prerequisites

	Python 3.10 or higher is recommended.

	pip (Python package installer).

1. Multi-Platform Installation

Open your terminal (Command Prompt/PowerShell for Windows) and follow these steps:
Step 1: Clone the Repository
Bash

git clone https://github.com/yourusername/syringe-pump-controller.git
cd syringe-pump-controller

Step 2: Install Dependencies

The GUI is built using Python's standard tkinter library and pyserial.
Bash

pip install pyserial

Important Note for Linux & Raspberry Pi OS:
Tkinter is often not included by default in Linux distributions. Please run:
Bash

sudo apt-get update
sudo apt-get install python3-tk

2. OS-Specific Instructions & Notes
💻 Windows

    Port Discovery: Look for COM ports (e.g., COM3) in the Device Manager.

    Python Path: Ensure "Add Python to PATH" was checked during installation.

🍎 macOS

    Miniconda/Anaconda Users: If you encounter errors like _tkinter not found, ensure you are using the base environment or have installed tk via conda.

    Security: You may need to grant "Input Monitoring" or "Serial Port" access depending on your macOS version.

🍓 Raspberry Pi OS / Linux

    Permissions: You might need permission to access the serial port. Add your user to the dialout group:
    Bash

    sudo usermod -a -G dialout $USER

    (Log out and log back in for changes to take effect.)

    CPU Load: On older Raspberry Pi models, high-frequency GUI updates might cause slight lag.

3. Usage
Setting up your Hardware

    Run the Config Generator to define your pump's mechanical settings (Steps/mm, Max Rate, etc.).
    Bash

    python config-generator_v1.py

    Save the file as config.json in the same directory as the main GUI.

Running the Controller
Bash

python SyringeGUI.py

⚠️ Critical Calibration Notes

    20kHz Limit: For Arduino Uno based setups, ensure your Max Rate does not exceed the theoretical limit calculated in the Config Generator. Exceeding 20kHz pulse frequency may cause the motor to stall or behave unpredictably.

    Invert Direction: Check the $3 setting in the Config Generator if your pump moves in the opposite direction.
