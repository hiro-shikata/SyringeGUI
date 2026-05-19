# SyringeGUI
Python-based GUI to control stepping motor-controlled syringe pumps.  

This project provides you with the tools to control DIY syringe pumps (max. 3 pumps) connected to Ardiuno device.  
<br>
<br>
## Hardware
	
- DIY **syringe pumps** consisted of **stepping motors (Bipolar/4-Wire)** and an actuator such as lead screws and slider. 
- As control devices, 1x **Arduino Uno/Nano** and **stepping motor drivers** (as many as needed) like DRV8825, A4988, etc.
- Option: CNC shield v3.0 for Arduino Uno or CNC shield v4.0 forr Arduino Nano  
  *You can use only the highest microstepping for your stepper driver with CNC shield v4.0 if the board is not modified.
- AC-to-DC converter (12V, at least 3A for 2 pumps)  
- **Any computers that can run Python 3.10 or higher** (Mac, Win, Linux, or Raspberry Pi)

You can find many good instructions on making DIY syringe pumps. To start this project, I was really impressed and inspired by the [**"poseidon"** system](https://github.com/pachterlab/poseidon).

1. https://github.com/pachterlab/poseidon  
2. https://www.instructables.com/DIY-Syringe-Pump/  
3. https://chem.uncg.edu/croatt/flow-chemistry/building-the-syringe-pump/  
4. https://reprap.org/wiki/Open-source_syringe_pump  
5. https://www.mass-spec.ru/projects/diy/syringe_pump/eng/  
  
Note: In this project, syringe pumps were obtained from a chinese company.  
<br>
<br>
### Technical Tips on Hardware preparation  
#### 1. Assembly of Arduino Uno + CNC shield v3.0 + motor drivers  
The details are well describe in [**posendon** system](https://github.com/pachterlab/poseidon). Here I just tell you techinical tips to adjust the **Vref** (reference voltage), which determines the maximum current flowing to the motor, for stepping motor drivers, such as DRV8825 and A4988. **This adjustment is important for making the most of motor function, while avoiding the overheating of the motors and drivers.**  
*For this process, you need an electrical tester (multimeter) to check the voltage.  

The following site could help you to calculate and set Vref.
https://www.circuitist.com/how-to-set-driver-current-a4988-drv8825-tmc2208-tmc2209/
<br>
<br>
##### Calulation of Vref

	Vref = Imax x Rs x C x RF
		Imax, rated current
		Rs, sense resistor values (DRV8825, 0.1Ω; A4988, 0.05-0.1Ω)
		C, coefficient specific to drivers (DRV8825, 5; A4988, 8) 
		RF, reducing factor to keep the circuit safe (typically 0.8-0.9)

To know the rated current, you can check the **datasheet of stepping motor**. 0.8-2.0 A for NEMA17 stepping motors, which are mostly used in DIY syringe pumps. **If you do not know the specs of your motor, first start 0.8A as Imax**. For DRV8825, values around 0.5V should be optimal to control NEMA17 motors. 

*Photo*
<br>
<br>
#### 2. Installation of GRBL Library into Arduino device
Before you run the **SyringeGUI** software, you needs to **flash Arduino with a sketch**, which includes script to control stepping motors with GRBL library.  

**Steps is following (at least for Ardiuno IDE 2.3.8 for mac):**  

1. Download [Arduino IDE](https://www.arduino.cc/en/software/) and install it.  
2. Download [GRBLv1.1h library (grbl-1.1h.20190825.zip)](https://github.com/gnea/grbl/releases).  
3. Unzip the ZIP file and find "grbl" folder in it, and then zip only this folder again.  
4. Open Ardiuno IDE -> Sketch -> Include Library -> Add .ZIP Library  
5. Find the zipped grbl file and select it.  
6. Select File tab -> Examples -> grbl (maybe you can find it at the bottom) -> grblUpload  
	*If you cannot find it, restart Arduino IDE and try #6.  
7. The sketch window will be opened.  
8. Connect Arduino Uno/Nano to PC with USB cable.  
9. Select Tools tab -> Board: -> find Arduino Uno or Nano  
10. Select Tools tab -> Port: -> find USB serial port connected to Arduino  
	(e.g., /dev/cu.usbserial-XXXX, /dev/cu.usbmodem-XXXX in mac; COMx in win)  
11. Press Upload button (maybe shown like Arrow(→)).  
12. Finaly your Arduino device is flush and ready to use.  


*photo*
<br>
<br>	
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
	
	- Alternatively, the packages(.app or .exe) are available for Mac and Win users.
	  As they were compiled with pyinstaller, Pyhon3 and its libararies are not needed.


### 1. Multi-Platform Installation (Python3 is required)  

Open your terminal (Command Prompt/PowerShell for Windows) and follow these steps: 

#### Step 1: Clone the Repository  

	Bash

    git clone https://github.com/hiro-shikata/SyringeGUI.git  
    cd SyringeGUI  

#### Step 2: Update Python3  

    pip3 install --upgrade pip  

If you have not installed Python3, please download from https://www.python.org/downloads/ and install it.

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

<br>
<br>	
### 2. OS-Specific Instructions & Notes

🍎 macOS

    Miniconda/Anaconda Users: If you encounter errors like _tkinter not found, ensure you are using the base environment or have installed tk via conda.

    Security: You may need to grant "Input Monitoring" or "Serial Port" access depending on your macOS version.

💻 Windows

    Port Discovery: Look for COM ports (e.g., COM3) in the Device Manager.

    Python Path: Ensure "Add Python to PATH" was checked during installation.


🍓 Raspberry Pi OS / Linux

    Permissions: You might need permission to access the serial port. Add your user to the dialout group:  
	
    Bash

    sudo usermod -a -G dialout $USER

    (Log out and log back in for changes to take effect.)

    CPU Load: On older Raspberry Pi models, high-frequency GUI updates might cause slight lag.

<br>
<br>	

### 2. Make config file to setting up your hardware

Run the **Config-Generator** App to define your pump's mechanical settings (Steps/mm, Max Rate, etc.).  
You can also modify these settings via Arduino IDE, but it would be easy to use this interactive App.

	Bash

	python3 --version         			# To know the version of installed Python3
    python3.XX config-generator_v1.py	# XX, the version

**Save the file as XXX.json (XXX, as you like) in the directory "~/SyringeGUI_Data/CONFIG".**  

- You can modify the exist JSON file with this App. So, it would be easier to load the distriuted JSON file "config.json" first.  
- You can generate and use multiple JSON file as you need (e.g., in case of different pump systems with one cotroller).  
- When no JSON files is in the directory, SyringeGUI will load internal default settings.  

*photo*

⚠️ Setting Notes

- **Rate Limitation**: For Arduino Uno/Nano based setups, ensure your Max Rate does not exceed the theoretical limit calculated in the Config Generator. Exceeding 20kHz pulse frequency may cause the motor to stall or behave unpredictably.

- **Invert Direction**: Check this setting in the Config-Generator if your pump moves in the opposite direction unexpectedly.

<br>
<br>

### 3. Run SyringeGUI (Controller App) 

	Bash

    python3.XX SyringeGUI.py

*photo*

#### 3.1 Connect to the USB serial port  
	
1. Move to Settings Tab.  
2. In Serial Port Settings, the tree will be displayed when clicked the combobox.  
3. Choose the same port as used in Arduino IDE (/dev/cu.usbserial-XXXX, /dev/cu.usbmodem-XXXX for mac, COMx for win, /dev/ttyACM0 for Raspberry Pi).   
4. Press Connect button.  
5. You can see the message in the Log window on Manual Tab.  
	**Once the connection has been establised, when you start App in the next time, the App will be automatically connected to Pumps.**  

#### 3.2 Synchronize the machine setting to Arduino device  

1. You can find Current Configration in Settings Tab. As defaul, internal defaul settings are used.  
2. Press **"Load Different Config JSON"**.  
3. Select the directory "~/SyringeGUI_Data/CONFIG" and choose the generated JSON file.  
4. After the file selection, only syringe list will be loaded.  
5. To synchronize the machine settings with the Arduino device, press **"Sync to Grbl EEPROM"**.  
6. You can see the message in the Log window on Manual Tab.  
	**Once the settings have been written in the Arduino device, Steps 3.2 are not needed to start SyringeGUI.**  

#### 3.3 (Option) Select the directory to save log and CSV files  

As defaul, the path "~/SyringeGUI_Data/" is selected for the save directory. You can change the directory as you like by pressing **"Select Directory"**.  
	**Once you select the directory, CSV file will be generated to save experimental settings. To apply it to Log file, you need restart SyringeGUI.**  

*photo*

#### 3.4 Manual Control Tab
In this tab, you can control syringe pumps manually.

1. **Choose Pumps**:  
   You can find checkbox on the top of three columns named Pump X, Y, and Z. When you check each of them ON, selected pumps can be activated to run.  

2. **Select Syringe**:  
   Syringes is listed in the combobox and one of them can be chosen.  

3. **Flow**:
   Input value determines the speed to inject or draw the syringe. When you put minus value on it, a pump moves in the opposite direction. When you change the units, the value will be automatically re-calculated. 

4. **Duration**:  
   Input value detemines the duration that a pump moves.  

5. **Max Vol.**:
   Input value determines the maximum volum that syringe can load. In the case that syringe is filled with a certain volume, it would be good to specify that value in this box. **When specified Flow x Duration is over Max Vol, the App does not run pumps.** 

6. **RUN/STOP X, Y, Z**:  
   Run each pump. **Note: When at least one pump has already started, you cannot start to run other pumps. This is technical limitation in this system.**  

7. **RUN/STOP ALL**:  
   RUN all the activated pumps simultaneously with specified each settings.  

8. **Reset Position**:  
   Current position and volume are displayed on the columns for each pumps. These values are set to 0 when the App starts. It would be good to press **"RESET POSITION"** when you start your experiment.  

9. **Jog**:  
    Jog control for each pumps. The rate is specified by moving the bar or write the value. Maximum and minimum rates are automatically restricted.  

10. **Log & Command window**:  
    Communications between the App and Arduino device are displayed here. You can also input some commands based on GRBL (e.g., $$ to see GRBL settings).  

*photo*

#### 3.5 Programmed Control  
In this tab, you can start sequential, complex programs to conrol pumps. To specify the sequnece recipe, you can load CSV files.  

The file needs to include the information as follow:
Pump, Start time (s), End time (s), Flow (µm/min)

	Examples: 
	
	X, 0, 60, 100
	X, 60, 120, 200
	Y, 0, 120, 100
	Z, 90, 120, 50


	Meanings:
	From 0 to 60 sec, Pumps X and Y move at 100 and 100 µm/min, respectively.
	From 60 to 90 sec, Pumps X and Y move at 200 and 100 µm/min, respectively.
	From 90 to 120 sec, PUmps X, Y, and Z move at 200, 100, and 50 µm/min, respectively.

* Note: only commas must be used to separate the values in the CSV files.  
  		No limitation for numbers of row.  
  		Only pumps specified in the CSV file move.  

1. **File Selection**:  
   You can choose a CSV file that records the sequence recipe. When the file is loaded, the recipe is displayed as the list and visualized patterns in the right panels.  

2. **Execution**:  
   **"START SEQUENCE"** to start the sequence recipe.  
   **"PAUSE"** if you want to pause the sequence.  
   **"RESUME"** to restart the sequence from the paused point.  
   **"ABORT"** for emergency stop and to restart the sequence recipe. 

*photo*

<br>
<br>

## ⚠️ Critical Calibration Notes  

To get more accuracy for pumping, the calibration is recommended. The procedure is as follow:  

1. Reset position.  
2. Measure the distance between the tabel/stage and lead screw end (or main body).  
3. Move the table/stage by Jog or RUN as far as possible (~ 10 cm). # Length: A mm  
4. Chech the position displayed on SyringeGUI and write it down. # Displayed position: X mm  
5. Measure the distance between the tabel/stage and lead screw end (or main body). # Length: B mm  
6. Calculate a calibrated Steps/mm value.  
   **Calibrated Steps/mm = Current Steps/mm * (X / Absolute(A-B))**  
7. Modify the JSON file with the calibrated value by using **Config-Generator_v1**.  
8. Load the JSON file in SyringeGUI and Sync the settings with Arduino.  
