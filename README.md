Documentation-
Roll, Pitch, Yaw extraction and Heading calculation
v1.0

Main Files Required
- main.py
- .json data file

Functions

- get_sec - 			outputs timestamps in seconds. Convert time in HH:MM:SS.SSSS format to seconds.
- euler_from_quaternion - 	takes in quaternion in (W,X,Y,Z) format and outputs Euler roll pitch and 
				yaw angles in [roll_x, pitch_y, yaw_z] format in radians.

Working

	- Loading the .json file (file name should be provided in the file_name variables
	- Extracting the [CORI] and [MAGN] data along with their timesteps and storing them in variables
	- Processing the quaternion format from the CORI data into euler form and storing the data in a numpy array
  	  using the euler_from_quaternion function
	- Saves the Plot of RPY values
	- Processing the MAGN data to identify the angle from the x, y components of magnetic field using
	  atan2(my/mx) operation and storing the value in degrees
	- Saves the Plot of Heading values
	- Creating new fields in the already opened .json file

	- New fields added under ['streams']
		- RPY
			- samples
				- values : [list of roll pitch yaw angles]
				- time : list of timestamps
		- HEAD
			- samples
				- values : [list of heading angles]
				- time : list of timestamps
	
	- saves the updated .json file with a specified name
_________________________________________________________________________________________________________________

Roll, Pitch, Yaw extraction and Heading calculation
v2.0

Main Files Required
- main2.py
- .json data file

Update

	- Heading is now calculated by creating a synchronized CORI data following the MAGN data
		Functioning - 
				an update index window is selected (eg 5)
				timestep differences in the range of index (i - window, i + window) of the CORI values
				index with the least difference is selected and corresponding quaternion value is appended
	- Method of Heading calculation is updated
		Formula used - 
				Mx = mx * cos(p) + my * sin(p)
				My = mx * cos(r) * sin(p) + my * cos(r) + mz * sin(r) * cos (p)
				M_yaw = atan2(My,Mx)

				mx = magnetometer x reading
				my = magnetometer y reading
				mz = magnetometer z reading
				r = roll angle
				p = pitch angle

