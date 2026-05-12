# SyringeGUI
Python-based GUI to control stepping motor-controlled syringe pumps.  

This project provides you with the tools to control DIY syringe pumps (max. 3 pumps) connected to Ardiuno device.  


## Hardware requirements
	
- DIY syringe pumps consisted of stepping motors and an actuator such as lead screws and slider. 
- As control devices, 1x Arduino Uno/Nano and stepping motor drivers (as many as needed) like DRV8825, A4988, etc.
- Option: CNC shield v3.0 for Arduino Uno or CNC shield v4.0 forr Arduino Nano  
  ** You can use only the highest microstepping for your stepper driver with CNC shield v4.0 if the board is not modified.
- Any computers that can run Python 3.10 or higher (Mac, Win, Linux, or Raspberry Pi)

You can find many good instructions on making DIY syringe pumps. To start this project, I was really impressed and inspired by the **"poseidon"** system.

1. https://github.com/pachterlab/poseidon  
2. https://www.instructables.com/DIY-Syringe-Pump/  
3. https://chem.uncg.edu/croatt/flow-chemistry/building-the-syringe-pump/  
4. https://reprap.org/wiki/Open-source_syringe_pump  
5. https://www.mass-spec.ru/projects/diy/syringe_pump/eng/  
  
Note: In this project, syringe pumps were obtained from a chinese company.  


### Tips on preparation of Hardware  
#### 1. Assembly of Arduino Uno + CNC shield v3.0 + motor drivers  
The details are well describe in link 1 (https://github.com/pachterlab/poseidon). Here I just tell you techinical tips to adjust the Vref (reference voltage) for stepping motor drivers, such as DRV8825 and A4988. This adjustment is important for making the most of motor function besides avoiding the heating of the motor and drivers. For this process, you need an electrical tester to check the voltage.  




#### 2. Installation of GRBL Library into Arduino


	
## Software Installation Guide

This project consists of two main tools:  

    SyringeGUI:
        The main controller for the syringe pumps.

    Config Generator:
        A utility to create and manage config.json for different mechanical setups and syringe types.

Prerequisites  

	- Python 3.10 or higher is recommended.  

	- pip (Python package installer).  

      This GUI is built using Python's standard tkinter library and pyserial.  


### 1. Multi-Platform Installation  

Open your terminal (Command Prompt/PowerShell for Windows) and follow these steps: 

#### Step 1: Clone the Repository

    git clone https://github.com/hiro-shikata/SyringeGUI.git
    cd SyringeGUI

#### Step 2: Update Python3

    pip3 install --upgrade pip

#### Step 3: Install Dependencies

    pip install pyserial

Important Note for Linux & Raspberry Pi OS:
Tkinter is often not included by default in Linux distributions.  
Please run:

    sudo apt update
    sudo apt install python3-pip
    pip3 install pyserial

    If you have a problem of installing pyserial, please try to install it on venv (virtualenv):
    python3 -m venv venv
    source venv/bin/activate
    pip install pyserial

### 2. OS-Specific Instructions & Notes
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

### 3. Usage
Setting up your Hardware

    Run the Config Generator to define your pump's mechanical settings (Steps/mm, Max Rate, etc.).
    Bash

    python config-generator_v1.py

    Save the file as config.json in the same directory as the main GUI.

Running the Controller
Bash
    python --version         # To know the version of Python3
    python3.XX SyringeGUI.py #XX is the version

⚠️ Critical Calibration Notes

    20kHz Limit: For Arduino Uno based setups, ensure your Max Rate does not exceed the theoretical limit calculated in the Config Generator. Exceeding 20kHz pulse frequency may cause the motor to stall or behave unpredictably.

    Invert Direction: Check the $3 setting in the Config Generator if your pump moves in the opposite direction.
