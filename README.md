# SyringeGUI
**Python-based GUI to control stepping motor-controlled syringe pumps.** 

This project provides you with the tools, **`SyringeGUI`** and its **`config-generator`**, to control DIY syringe pumps (max. 3 pumps) connected to an Arduino device.  
<div align="center">
<img src="https://github.com/hiro-shikata/SyringeGUI/blob/main/media/SyringeGUI_icon.png" width="150px"> <img src="https://github.com/hiro-shikata/SyringeGUI/blob/main/media/config-generator_icon.png" width="150px">
</div>

The coding for this project was assisted by AI. Please feel free to report any bugs to help me improve it.

<div align="center">
<img src="https://github.com/hiro-shikata/SyringeGUI/blob/main/media/SyringeGUI_programmed-control_recipe-loaded.jpg" width="800px">
<img src="https://github.com/hiro-shikata/SyringeGUI/blob/main/media/cg_calculate-values.jpg" width="600px">
</div>
<br>
<br>

## Hardware
	
- DIY **syringe pumps** consisting of **stepping motors (Bipolar/4-Wire)** and an actuator such as lead screws and sliders. 
- Control devices: 1x **Arduino Uno/Nano** and **stepping motor drivers** (as many as needed) like DRV8825, A4988, etc.
- Option: CNC shield v3.0 for Arduino Uno or CNC shield v4.0 for Arduino Nano  
  *Note: You can only use the highest microstepping for your stepper driver with the CNC shield v4.0 unless the board is modified.*
- AC-to-DC converter (12V, at least 3A for 2 pumps).  
- **Any computer that can run Python 3.10 or higher** (Mac, Win, Linux, or Raspberry Pi).

You can find many great instructions on making DIY syringe pumps. To start this project, I was highly impressed and inspired by the [**"poseidon"**](https://github.com/pachterlab/poseidon) system.

1. https://github.com/pachterlab/poseidon  
2. https://www.instructables.com/DIY-Syringe-Pump/  
3. https://chem.uncg.edu/croatt/flow-chemistry/building-the-syringe-pump/  
4. https://reprap.org/wiki/Open-source_syringe_pump  
5. https://www.mass-spec.ru/projects/diy/syringe_pump/eng/  
  
Note: In this project, the mechanical syringe pump parts were obtained from a Chinese company.

<br>
<br>

### Technical Tips on Hardware preparation  
#### 1. Assembly of Arduino Uno + CNC Shield v3.0 + Motor Drivers
The details are well described in [**poseindon** system](https://github.com/pachterlab/poseidon). Here I just tell you techinical tips to adjust the **Vref** (reference voltage), which determines the maximum current flowing to the motor, for stepping motor drivers, such as DRV8825 and A4988. **Proper adjustment is critical to maximize motor performance while avoiding the overheating of the motors and drivers.**  
* For this process, you will need a multimeter (electrical tester) to check the voltage.  

The following site could help you to calculate and set Vref.
https://www.circuitist.com/how-to-set-driver-current-a4988-drv8825-tmc2208-tmc2209/
<br>
<br>

##### Calculation of Vref

> **`Vref = Imax × Rs × C × RF`**
> - **Imax**: Rated current of the motor
> - **Rs**: Sense resistor value (DRV8825: `0.1Ω`, A4988: `0.05-0.1Ω`)
> - **C**: Coefficient specific to drivers (DRV8825: `5`, A4988: `8`) 
> - **RF**: Reducing factor to keep the circuit safe (typically `0.8` - `0.9`)

To find the rated current, check the **datasheet of your stepping motor**. It is typically 0.8 - 2.0 A for NEMA17 stepping motors, which are commonly used in DIY syringe pumps. **If you do not know the specifications of your motor, start with 0.8A as Imax for safety**. For the DRV8825, a Vref value around 0.5V is usually optimal for controlling standard NEMA17 motors.

<div align="center">
<img src="https://github.com/hiro-shikata/SyringeGUI/blob/main/media/Vref-adjustment.jpg"  width="600px">
</div>
<br>
<br>

#### 2. Installation of GRBL Library into the Arduino Device
Before running the **SyringeGUI** software, you need to **flash the Arduino with a sketch** that includes the script to control stepping motors via the GRBL library.  

**Steps (Verified on Arduino IDE 2.3.8 for macOS):**  
1. Download and install the [Arduino IDE](https://www.arduino.cc/en/software/).  
2. Download the [GRBL v1.1h library (grbl-1.1h.20190825.zip)](https://github.com/gnea/grbl/releases).  
3. Unzip the ZIP file and find the internal "grbl" folder, zip **only** this internal folder again.   
4. Open Arduino IDE -> `Sketch` -> `Include Library` -> `Add .ZIP Library...`    
5. Select the zipped `grbl` file you just created.    
6. Select `File` tab -> `Examples` -> `grbl` (usually found at the bottom) -> `grblUpload`.  
	*If you cannot find it, restart the Arduino IDE and try step 6 again.*  
7. A new sketch window will open.  
8. Connect your Arduino Uno/Nano to your computer using a USB cable.  
9. Select `Tools` tab -> `Board:` -> Select **Arduino Uno** or **Nano**.  
10. Select `Tools` tab -> `Port:` -> Select the USB serial port connected to the Arduino.  
	*(e.g., `/dev/cu.usbserial-XXXX` or `/dev/cu.usbmodem-XXXX` on Mac; `COMx` on Windows)*  
11. Click the **Upload** button (indicated by the right arrow icon `→`).  
12. Once completed, your Arduino device is successfully flashed and ready to use!  

<div align="center">
<img src="https://github.com/hiro-shikata/SyringeGUI/blob/main/media/Arduino%20IDE.jpg"  width="600px">
</div>
<br>
<br>	

## Software Installation Guide  

This project consists of two main tools:  

- **SyringeGUI**: The main controller application for the syringe pumps.  
- **Config Generator**: A utility to create and manage the `config.json` file for different mechanical setups and syringe types.  

Prerequisites  

- Python 3.10 or higher is recommended.  
- pip (Python package installer).  

  *This GUI is built using Python's standard `tkinter` library and `pyserial`.*  
    
  *Alternatively, standalone pre-compiled packages (`.app` for Mac / `.exe` for Windows) are available. Since they are compiled with PyInstaller, Python 3 and its libraries are not required to run them.*  


### 1. Multi-Platform Installation (Using Python 3)  

Open your terminal (Command Prompt/PowerShell for Windows) and follow these steps:  

#### Step 1: Clone the Repository or Download Files  

	bash

	git clone [https://github.com/hiro-shikata/SyringeGUI.git](https://github.com/hiro-shikata/SyringeGUI.git)  
	cd SyringeGUI

#### Step 2: Update Python3  

    pip3 install --upgrade pip  

If you have not installed Python3, please download and install it from [python.org](https://www.python.org/downloads/) 

#### Step 3: Install Dependencies  

    pip install pyserial  

Important Note for Linux & Raspberry Pi OS:
Tkinter is often not included by default in Linux distributions.  
Please run:  

    sudo apt update  
    sudo apt install python3-pip  
    pip3 install pyserial  

If you encounter issues installing `pyserial`, it is recommended to install it within a virtual environment (`venv`):

    python3 -m venv venv  
    source venv/bin/activate  
    pip install pyserial  

<br>
<br>	

### 2. OS-Specific Instructions & Notes

🍎 macOS

Miniconda/Anaconda Users: If you encounter errors like `_tkinter not found`, ensure you are using the `base` environment or have installed `tk` via conda (`conda install tk`).

Security: You may need to grant "Input Monitoring" or "Serial Port" access depending on your macOS version.  

<br>

💻 Windows

Port Discovery: Look for COM ports (e.g., `COM3`) in the Device Manager.

Python Path: Ensure "Add Python to PATH" was checked during installation.  
  
<br>

🍓 Raspberry Pi OS / Linux  

Permissions: You might need permission to access the serial port. Add your user to the `dialout` group:  
	
    Bash

    sudo usermod -a -G dialout $USER

    (Please Log out and log back in for changes to take effect.)

    CPU Load: On older Raspberry Pi models, high-frequency GUI updates might cause slight lag. 

If you use `venv` to install `pyserial`, you need to activate `venv` before running `SyringeGUI.py`.  

	Bash

	source /home/USER/venv/bin/activate		# Replace USER with your USER directory
	
	python3 /home/PATH/SyringeGUI_raspi.py	# Replace PATH with your path to locate the `SyringeGUI`
  
*Alternatively, you can use `Desktop Entry` as a shootcut to run `SyringeGUI` without operating `Terminal`. Please replace PATH on the distributed `SyringeGUI.desktop` file with your correct path. Then, please place the file on your desktop or somewhere and just click it.*  
  

*The code for Raspberry Pi OS is distributed as `Syringe_GUI_raspi.py`, where the GUI appearance is optimized for `Raspberry Pi 7-inch Touch Screen Display` or its alternatives.*  

<br>
<br>	

### 2. Setting Up Your Hardware Config File

Run the `config-generator` app to define your pump's mechanical settings (Steps/mm, Max Rate, etc.). While you can modify these settings via the Arduino IDE, using this interactive app is much easier.  

	Bash

	python3 --version         			# Check the installed Python 3 version
    python3.XX config-generator_v1.py	# Replace XX with your actual version (e.g., python3.10)

<div align="center">
<img src="https://github.com/hiro-shikata/SyringeGUI/blob/main/media/cg_input-value.jpg" width="500px"> <img src="https://github.com/hiro-shikata/SyringeGUI/blob/main/media/cg_calculate-values.jpg" width="500px">
</div>

1. At **Tab 1: Pump Settings**, please choose a method to specify the **`Steps/mm` value**, which is the most crucial setting for this system.
   - **A. Step Angle**: Stepping motors rotate at a specific angle (e.g., 0.9°, 1.8°, or 18°) per step (pulse) received from the Arduino device. Please check the specifications of your stepping motor. For standard NEMA17 motors, this angle is typically **`1.8°`**.   
   - **B. Microstepping**: Specify the microstepping setting configured on your motor driver. This is determined by the jumper pin configuration on your CNC shield and the driver's specifications. For example, when using a DRV8825 driver on a CNC shield v3.0 with M0, M1, and M2 all set to HIGH (all three jumper pins set), it enables **`1/32`** microstepping.

<div align="center">
<img src="https://github.com/hiro-shikata/SyringeGUI/blob/main/media/microstepping_DRV8825-on-CNCshieldv3.jpg" width="350px"> 
</div>

   - **C. Gear Ratio**: This setting is optional. Since general DIY syringe pumps do not utilize gears, simply enter **`1`** in this box. If your specific hardware setup includes a gear assembly between the motor and the lead screw, please specify that precise ratio.  
   - **D. Lead Screw Pitch**: You can enter the pitch value directly, or calculate it by measuring the number of threads within a specific physical length.  

<div align="center">
<img src="https://github.com/hiro-shikata/SyringeGUI/blob/main/media/measure-pitch.jpg" width="350px"> <img src="https://github.com/hiro-shikata/SyringeGUI/blob/main/media/cg_how-to-calculate-leadscrew-pitch.jpg" width="350px">
</div>

2. Specify the values for **`Max rate (mm/min)`**, **`Accel (mm/sec²)`**, and **`Max Travel Distance (mm)`** according to the on-screen  instructions.  
3. Fill out the settings for all active pumps. Alternatively, you can check the box at the top to instantly copy the configuration of Pump X to the other pump columns.  
4. At **Tab 2: Syringe Settings**, you can register and manage your syringe profiles. You only need to provide a **`Name`**, **`Volume (mL)`**, and **`Length (mm)`** for each syringe.  

<div align="center">
<img src="https://github.com/hiro-shikata/SyringeGUI/blob/main/media/measure-syringe.jpg" width="400px"> 
</div>
<br>
<div align="center">
<img src="https://github.com/hiro-shikata/SyringeGUI/blob/main/media/cg_how-to-add-syringe.jpg" width="500px"> <img src="https://github.com/hiro-shikata/SyringeGUI/blob/main/media/cg_updated-syringe-list.jpg" width="500px">
</div>

   **Tip for Accuracy: For the highest precision, it is highly recommended to calibrate this value by measuring the weight of the dispensed water using a precision weighing scale (mass-to-volume calibration).**
   6. 5. Click **`Generate New Config File`** to save your settings. Save the generated file as `XXX.json` (replace XXX with your desired configuration name) into the directory **`~/SyringeGUI_Data/CONFIG`**.  
  
- You can also modify existing JSON files using this app. It is easier to load the distributed default `onfig.json` first.  
- You can generate and use multiple JSON files as needed (e.g., if you run different pump systems with a single controller).  
- If no JSON files are found in the directory, SyringeGUI will automatically fall back to its internal default settings.  




⚠️ Setting Notes

- **Rate Limitation**: For Arduino Uno/Nano based setups, ensure your Max Rate does not exceed the theoretical limit calculated in the `config-generator_v1`. Exceeding a 20kHz pulse frequency may cause the stepper motor to stall or behave unpredictably.

- **Invert Direction**: Check this setting in the `config-generator_v1` if your pump moves in the opposite direction than expected.

<br>
<br>

### 3. Run SyringeGUI (Controller App)

	Bash

    python3.XX SyringeGUI.py


#### 3.1 Connect to the USB serial port  
<div align="center">
<img src="https://github.com/hiro-shikata/SyringeGUI/blob/main/media/SyringeGUI_settings.jpg" width="600px">
</div>

1. Navigate to the `Settings` tab.  
2. In the Serial Port Settings section, click the combobox to display the available port tree.  
3. Choose the same port used in the Arduino IDE (`/dev/cu.usbserial-XXXX` / `/dev/cu.usbmodem-XXXX` on Mac, `COMx` on Windows, `/dev/ttyACM0` on Raspberry Pi).   
4. Click the `Connect` button.  
5. You can monitor the connection status message in the `Log` window on the `Manual` tab.  
	**Once the connection is successfully established, the app will automatically connect to the pumps on the next startup.**  

#### 3.2 Synchronize the machine setting to Arduino device  

1. You can review the `Current Configuration` in the `Settings` tab. By default, the internal default settings are applied.  
2. Click **`Load Different Config JSON`**.  
3. Navigate to the directory `~/SyringeGUI_Data/CONFIG` and choose your generated JSON file.  
4. After selecting the file, only the syringe list will be loaded into the UI.  
5. To synchronize the mechanical settings with the Arduino device, click **`Sync to Grbl EEPROM`**.  
6. You will see a confirmation message in the Log window on the `Manual` tab.  
	**Once these settings are written to the Arduino's EEPROM, you do not need to repeat step 3.2 on subsequent launches of SyringeGUI.**  

#### 3.3 (Option) Select the Directory to Save Log and CSV Files  

By default, the path `~/SyringeGUI_Data/` is selected as the default save directory. You can change this destination folder at any time by clicking **`Select Directory`**.  
	**Once you select a new directory, CSV files for experimental settings will be generated there immediately. To apply the new path to the main system log file, you will need to restart SyringeGUI.**  

*photo*

#### 3.4 Manual Control Tab
Manually control your syringe pumps using the following features:
<div align="center">
<img src="https://github.com/hiro-shikata/SyringeGUI/blob/main/media/SyringeGUI_manual-control.jpg" width="800px">
</div>

1. **Choose Pumps**:  
   Checkboxes are located at the top of the three columns named Pump X, Y, and Z. Checking them activates the respective pump for operation.  

2. **Select Syringe**:  
   Select your syringe type from the populated combobox list.  

3. **Flow**:
   Input the desired flow rate speed to inject or draw. Entering a negative value will move the pump in the opposite direction. Changing the unit automatically recalculates the flow rate value. 

4. **Duration**:  
   Defines the total operating run time for the pump.  

5. **Max Vol.**:
   Specifies the maximum volume capacity the syringe can handle. If your syringe is partially filled, set that specific limit here. **If the calculated volume (Flow × Duration) exceeds the Max Vol, the app will block the pump execution for safety.** 

6. **RUN/STOP X, Y, Z**:  
   Runs each pump individually. **Note: If at least one pump is already running, you cannot start another individual pump. This is a technical hardware limitation of the current GRBL setup.**  

7. **RUN/STOP ALL**:  
   Runs all activated pumps simultaneously using their respective individual settings.  

8. **Reset Position**:  
   Displays the current real-time position and volume for each pump. These values initialize to 0 when the app starts. It is good practice to click **`RESET POSITION`** before starting a new experiment.  

9. **Jog**:  
    Provides manual jog controls for fine adjustments. Adjust the rate using the slider bar or input a precise numerical value. Maximum and minimum jog rates are automatically bounded.  

10. **Log & Command window**:  
    Displays real-time serial communication between the app and the Arduino. You can also manually input GRBL-supported hex commands (e.g., enter `$$` to view the active GRBL core settings).  


#### 3.5 Programmed Control  
Execute sequential, complex automated profiles using this tab. You can load a custom CSV file to specify your sequence recipes.  
<div align="center">
<img src="https://github.com/hiro-shikata/SyringeGUI/blob/main/media/SyringeGUI_programmed-control.jpg" width="600px">
</div>

1. **File Selection**:  
   Click to choose your sequence recipe CSV file. Once loaded, the steps are populated as an preview list and visually mapped on the right panels.   

The configuration CSV file must follow this exact format:  
`Pump, Start time (s), End time (s), Flow (µm/min)`  

	Example recipe: 
	
	X, 0, 60, 100
	X, 60, 120, 200
	Y, 0, 120, 100
	Z, 90, 120, 50
  
*Note: Only commas (`,`) must be used as delimiters to separate values in the CSV file.*  
*Note: There is no restriction on the number of sequence rows.*  
*Note: Only the specific pumps declared in the CSV recipe will engage in motion.*  

<img src="https://github.com/hiro-shikata/SyringeGUI/blob/main/media/CSV_example.jpg" width="400px">

**How it executes:**
- **From 0 to 60 sec**: Pump X moves at 100 µL/min, and Pump Y moves at 100 µL/min.
- **From 60 to 90 sec**: Pump X accelerates to 200 µL/min, while Pump Y continues at 100 µL/min.
- **From 90 to 120 sec**: Pump X runs at 200 µL/min, Pump Y runs at 100 µL/min, and Pump Z joins at 50 µL/min.

2. **Execution**:  
   **"START SEQUENCE"**: Begin the sequence run.  
   **"PAUSE"**: Temporarily pauses the running sequence.  
   **"RESUME"**: Restarts the sequence precisely from the paused timestamp.  
   **"ABORT"**: Triggers an emergency stop and resets the sequence recipe completely. 
 
<div align="center">
<img src="https://github.com/hiro-shikata/SyringeGUI/blob/main/media/SyringeGUI_programmed-control_recipe-loaded.jpg" width="600px">
</div>
 
<br>
<br>

## ⚠️ Critical Calibration Notes  

To achieve maximum pumping accuracy, performing a physical calibration is highly recommended. Use the following procedure:  
  
1. Click **`Reset Position`** in the UI.  
2. Physically measure the exact distance between the moving table/stage and the end of the lead screw (or main frame body).  
3. Move the stage as far as possible (~ 100 mm) using either the Manual **`RUN`** or **`Jog`** controls. `Physical Distance Travelled: A mm`    
4. Check the software position displayed on SyringeGUI and record it. `Displayed Position: X mm`  
5. Re-measure the physical distance between the table/stage and the frame body. `Remaining Distance: B mm`  
6. Calculate your new calibrated Steps/mm value using this formula:  
   **`Calibrated Steps/mm = Current Steps/mm × (X / |A - B|)`**  
7. Launch the **`Config-Generator`** utility, open your JSON config file, and update the Steps/mm field with this new calibrated value. 
8. Save the file, reload it into SyringeGUI, and click **`Sync to Grbl EEPROM`** to commit the change to your hardware.

<div align="center">
<img src="https://github.com/hiro-shikata/SyringeGUI/blob/main/media/before.jpg" width="300px"> <img src="https://github.com/hiro-shikata/SyringeGUI/blob/main/media/after.jpg" width="330px"> <img src="https://github.com/hiro-shikata/SyringeGUI/blob/main/media/SyringeGUI_calibration.jpg" width="310px"> 
</div>

In this case, current Steps/mm value was 6500. Caliburated value = 6500 x (100 / |14.20 - 115.75|) = 6400.8 Steps/mm
<br>
<br>

# License  
Licensed under the MIT License.  

<br>
<br>

# Fundings  
This project was supported by the grants from the `Japan Society for the Promotion of Science` (Grant# JP24H01499) and the `Kato Memorial Bioscience Foundation`.  
<br>

<div align="center">
<img src="https://github.com/hiro-shikata/SyringeGUI/blob/main/media/whole-system.jpg" width="600px">
</div>
