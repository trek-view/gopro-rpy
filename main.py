import json
import numpy as np  
#import imufusion
import matplotlib.pyplot as plt
#from scipy.spatial.transform import Rotation
import math

def get_sec(time_str):
    # Get seconds from time in hours,minutes,sec
    h, m, s = time_str.split(':')
    return float(h) * 3600 + float(m) * 60 + float(s)

def euler_from_quaternion(w, x, y, z):

        x = x #change to -x if needed
        """
        Convert a quaternion into euler angles (roll, pitch, yaw)
        roll >> around x in radians (counterclockwise)
        pitch >> around y in radians (counterclockwise)
        yaw >> around z in radians (counterclockwise)
        """
        t0 = +2.0 * (w * x + y * z)
        t1 = +1.0 - 2.0 * (x * x + y * y)
        #roll_x = math.atan2(t0, t1)*(180/math.pi) #deg
        roll_x = math.atan2(t0, t1) #rad
     
        t2 = +2.0 * (w * y - z * x)
        t2 = +1.0 if t2 > +1.0 else t2
        t2 = -1.0 if t2 < -1.0 else t2
        #pitch_y = math.asin(t2)*(180/math.pi) #deg
        pitch_y = math.asin(t2) #rad
     
        t3 = +2.0 * (w * z + x * y)
        t4 = +1.0 - 2.0 * (y * y + z * z)
        #yaw_z = math.atan2(t3, t4)*(180/math.pi) # deg
        yaw_z = math.atan2(t3, t4) # rad
     
        return [roll_x, pitch_y, yaw_z] # in radians
    
# Loading the .json file
file_name = 'GS016143-full-telemetry.json'
f = open(file_name)
  
# returns JSON object as a dictionary
data = json.load(f)

# loading the relevant data in relevant variables

cam_data = data['1']['streams']['CORI']["samples"]
mag_data = data['1']['streams']['MAGN']["samples"]

# extracting timestamps and data for the relevant variables
timestamp_cam = []
cam_val = []
for i in range(len(cam_data)):
    timestamp_cam.append(get_sec(cam_data[i]['date'].split('T')[1][:-1]))
    cam_val.append(cam_data[i]['value']) # [W,X,Y,Z]
cam_ori_val = np.array(cam_val)
#print(np.shape(cam_ori_val))

mag_val = []
timestamp_mag = []
for i in range(len(mag_data)):
    timestamp_mag.append(get_sec(mag_data[i]['date'].split('T')[1][:-1]))
    mag_val.append(mag_data[i]['value']) # in uT
mag_val = np.array(mag_val)
#print(np.shape(mag_val))

# processing camera orientation
rpy_arr = []
for i in range(len(cam_ori_val)):
    rpy_arr.append(euler_from_quaternion(cam_ori_val[i][0],cam_ori_val[i][3],cam_ori_val[i][1],cam_ori_val[i][2]))
rpy_arr = np.array(rpy_arr)*(180/math.pi)


# plot RPY
plt.figure()
plt.plot(timestamp_cam,rpy_arr[:,0],timestamp_cam,rpy_arr[:,1],timestamp_cam,rpy_arr[:,2])
plt.title('Camera Roll, Pitch and Yaw angle variance')
plt.legend(['Roll','Pitch','Yaw'])
plt.xlabel('Time(s)')
plt.ylabel('Angle')
plt.savefig('RPY2.png')

# processing Magnetic heading

# syncing acc data based on mag data

cam_val_syc = []
timestamp_cam_syc = []
window = 5
for i in range(len(timestamp_mag)):
    ts_m = timestamp_mag[i]
    if window > i:
        min_ind = 0
    else:
        min_ind = i - window
    if (i+window)>len(timestamp_cam):
        max_ind = len(timestamp_cam)
    else:
        max_ind = i + window
    diff_arr = []
    ind_exp = []
    for j in range(min_ind, max_ind):
        diff = timestamp_cam[j] - timestamp_mag[i]
        diff_arr.append(diff)
        ind_exp.append(j)
    #print(ind_exp)
    if len(ind_exp)>0:
        min_diff_ind = diff_arr.index(min(diff_arr,default='EMPTY'))
        min_val_list_ind = ind_exp[min_diff_ind]
    else:
        #print('case2')
        min_diff_ind = max_ind-1
        min_val_list_ind = max_ind-1
    cam_val_syc.append(cam_val[min_val_list_ind])
cam_val_syc = np.array(cam_val_syc)
mag_val = np.array(mag_val)
#print(len(cam_val_syc))
#print(len(mag_val))

# heading calc in 3D using RPY

calc_heading = []
for i in range(len(timestamp_mag)):
    rpy = euler_from_quaternion(cam_val_syc[i][0],cam_val_syc[i][3],cam_val_syc[i][1],cam_val_syc[i][2])
    Mx = mag_val[i,1]*math.cos(rpy[1]) + mag_val[i,2]*math.sin(rpy[1])
    My = mag_val[i,1]*math.sin(rpy[0])*math.sin(rpy[1]) + mag_val[i,2]*math.cos(rpy[0]) - mag_val[i,0]*math.sin(rpy[0])*math.cos(rpy[1])
    M_yaw = math.atan2(My,Mx)
    calc_heading.append(M_yaw*(180/math.pi))

# plot heading
plt.figure()
plt.plot(timestamp_mag,calc_heading)
plt.title('Camera Compass Heading Angle')
plt.ylim(-180,180)
plt.xlabel('Time(s)')
plt.ylabel('Compass Angle (rad)')
plt.savefig('heading2.png')

# update the json file

rpy_dict = {'values':rpy_arr.tolist(),'time':timestamp_cam}
rpyval_dict = {'samples':rpy_dict}
#rpy_time = {'time':timestamp_cam}
head_dict = {'values':calc_heading,'time':timestamp_mag}
headval_dict = {'samples':head_dict}
#head_time = {'time':timestamp_mag}
json.dumps([rpy_dict,head_dict])
#json.dumps(rpy_time)
#json.dumps(head_dict)
#json.dumps(head_time)


data['1']['streams']['RPYV'] = rpy_dict
#data['1']['streams']['RPYV']['timestamp'] = rpy_time
data['1']['streams']['HEAD'] = head_dict
#data['1']['streams']['HEAD']['timestamp'] = head_time

updated_file = json.dumps(data)
f2 = open("telemetry_updated.json",'a')
f2.write(updated_file)
f2.close()
f.close()

