# GoPro RPY

A proof-of-concept to use gopro-telemetry to automatically adjust roll, pitch, and yaw in processed equirectangular videos/

Read this post for a bit more information about our thought processes in building this: https://www.trekview.org/blog/2022/calculating-heading-of-gopro-video-using-gpmf-part-1/

## Prerequisites

1. First extract the telemetry file (as json) from your GoPro video using [gopro-telemetry](https://github.com/JuanIrache/gopro-telemetry/). [Detailed instructions about how to do this can be found in this post](https://www.trekview.org/blog/2022/gopro-telemetry-exporter-getting-started/).
2. Install required packages `pip3 install -r requirements.txt`

## Usage

add arguments in command line

```shell
python3 main.py [.json file name/ file path] [--plot True]
```

`--plot` argument is optional, only put some value when plots are required

### Example usage

#### 1. To just update the .json file with new data

```shell
python3 main.py	GS019049.json
```

#### 2. To update the .json file with new data and create plots of the roll pitch yaw and magnetic heading 

```shell
python3 main.py	GS019049.json --plot true
```

#### 3. To adjust yaw of video processed with World Lock mode = true to original of a 360 video

```shell
python3 main.py	GS010013-worldlock.json --video_input GS010011-worldlock.mp4 --mode yaw
```

#### 4. To automatically level the horizon using roll of a 360 video

```shell
python3 main.py	GS010011-roll.json --video_input GS010011.mp4 --mode roll
```

#### 5. To automatically level the horizon using roll of a 360 video

```shell
python3 main.py	GS010010-pitch.json --video_input GS010010.mp4 --mode pitch
```

## Camera support

This script has been tested and confirmed working for:

* GoPro MAX running firmware: H19.03.02.00.00 (shows on camera LCD as 02.00)

## How it works

### 1. Calculating yaw, pitch and roll values

Camera orientation `CORI` is a relative measurement (the orientation relative to the orientation the sensor had when the acquisition started). It is reported in Quaternions in the order `w`,`x`,`y`,`z` in gopro-telemetry.

```json
"CORI":{
  "samples":[{
    "value":[0.9989318521683401,-0.024964140751365705,0.02621539963988159,0.029206213568529312],
    "cts":176.62,
    "date":"2022-05-26T08:35:42.485Z",
    "sticky":{
      "VPTS":1261037}
    },
```

To calculate yaw, pitch and roll values from this data we take the four Quarternation values (Euler Parameters) and convert them into Euler angles on each axis.

The equations to do this are somewhat complex, as you'll see from a cursory scan of this Wikipedia article; [Conversion between Quaternions and Euler angles](
https://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles), or by examining the code in `main.py`.

### 2. Calculating heading values

Values from the Magnetometer are reported in the axis order `z`,`x`,`y` in MicroTeslas in gopro-telemetry. 

```json
"MAGN":{
	"samples":[{
		"value":[-4,88,27],
		"cts":163.461,
		"date":"2022-05-26T08:35:42.485Z"
	},
```

To calculate heading values we first sync `MAGN` samples with their closest `CORI` sample.

Once the times have been synced and each `MAGN` sample has a corresponding `CORI` sample we can calculate the magnetic heading using the formula:

```
Mx = mx * cos(p) + my * sin(p)
My = mx * cos(r) * sin(p) + my * cos(r) + mz * sin(r) * cos (p)
M_yaw = atan2(My,Mx)
```

Where:

* `mx` = magnetometer x reading
* `my` = magnetometer y reading
* `mz` = magnetometer z reading
* `r` = roll angle
* `p` = pitch angle

_Be careful not to confuse `My` and `my` / `Mx` and `mx` (they are different variables). For clarity; `my` is the magnetic component in y direction, `My` is the output of the second equation which is approximately corrected y component of the magnetic field. The same explanation applies for `Mx` and `mx`._

### 3. Writing new values to gopro-telemetry

This script then writes out a new telemetry file (`INPUT-calculated.json`) with the following values:

* `RPYR`:
	* name: roll, pitch, yaw (x,y,z)
	* units: radians
	* cts: milliseconds since video start
	* date: YYYY-MM-DDTHH:MM:SS.SSSZ
* `RPYD`
	* name: roll, pitch, yaw (x,y,z)
	* units: degrees
	* cts: milliseconds since video start
	* date: YYYY-MM-DDTHH:MM:SS.SSSZ
* `HEAR`
	* name: magnetic heading
	* units: radians
	* cts: milliseconds since video start
	* date: YYYY-MM-DDTHH:MM:SS.SSSZ
* `HEAD`
	* name: magnetic heading
	* units: degrees
	* cts: milliseconds since video start
	* date: YYYY-MM-DDTHH:MM:SS.SSSZ

#### Notes on calculated data

For reference, here's a sample of the first and last `HEAD` entry in a telemetry file to demo the structure of the object;

```json
"HEAD": {
	"samples": [
		{
			"value": 2.4325704405863235,
			"cts": 189.758,
			"date": "2022-06-08T11:46:54.225Z"
		},
```

...


```json
		{
			"value": -1.9311572331906321,
			"cts": 21121.995333333347,
			"date": "2022-06-08T11:47:15.591Z"
		}
	],
	"name": "magnetic heading",
	"units": "degrees"
	}
},
```

You can see the `-calculated.json` files with all fields listed in the `/docs` directory of this repository.

##### Magnetic Heading (`HEAD`)

Values between `-180` and `180` (`0` is North) (degrees)

Graphs shown below for example Roll, Pitch, Yaw videos.

##### (x) Roll (`RPYD`)

Values between `-180` and `180` (degrees).

Video input:

<iframe width="560" height="315" src="https://www.youtube-nocookie.com/embed/GDtz_K6k-Dg" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

Output of script (using `--plot True`):

![RPY GS010011.mp4](/docs/GS010011-roll-RPY.png)

![Magnetic heading GS010011.mp4](/docs/GS010011-roll-heading.png)

Adjusted video using `--mode roll`:

TODO

##### (y) Pitch (`RPYD`)

Values between `-90` and `90` (degrees).

<iframe width="560" height="315" src="https://www.youtube-nocookie.com/embed/xCjSPYIKN68" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

Output of script (using `--plot True`):

![RPY GS010010.mp4](/docs/GS010010-pitch-RPY.png)

![Magnetic heading GS010010.mp4](/docs/GS010010-pitch-heading.png)

Adjusted video using `--mode pitch`:

TODO

##### (z) Yaw (`RPYD`)

Values between `-180` and `180` (degrees)

<iframe width="560" height="315" src="https://www.youtube-nocookie.com/embed/kBlqZx21_6g" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

![RPY GS010012.mp4](/docs/GS010012-yaw-RPY.png)

![Magnetic heading GS010012.mp4](/docs/GS010010-yaw-heading.png)

Adjusted video using `--mode yaw`:

TODO

### 4. Use to level / adjust video

TODO

## Support

Community support available on Discord: https://discord.gg/ZVk7h9hCfw

## License

The code of this site is licensed under a [MIT License](/LICENSE).
