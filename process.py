import ffmpeg
import os
import shutil

frame_rate_str = '25'
frame_rate = 25
extract_dir = '.'
video_dir = '.'
video_filename = ''

# Extract frames
def extract(videopath):
    global frame_rate, frame_rate_str, extract_dir, video_dir, video_filename

    try:
        streams = ffmpeg.probe(videopath)['streams']
        for stream in streams:
            if stream['codec_type'] == 'video':
                frame_rate_str = stream['r_frame_rate']
                rate = frame_rate_str.split('/')
                frame_rate = int(rate[0])
                if len(rate) > 1:
                    frame_rate = frame_rate / int(rate[1])
                break
    except ffmpeg.Error as e:
        print(e.stderr)
        exit()

    print('frame rate:', frame_rate_str, 'rate:', frame_rate)

    video_dir, video_filename = os.path.split(videopath)
    extract_dir = os.path.join(video_dir, 'FRAMES')
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    os.mkdir(extract_dir)
    os.system("ffmpeg -hide_banner -i " + videopath + " -r " + frame_rate_str + " -q:v 2 " + extract_dir + "/%9d.jpg")

def adjust_heading(data, mode="unworldlock"):
    global extract_dir, frame_rate, video_dir, frame_rate_str, video_filename
    frames = [f for f in os.listdir(extract_dir)]
    work_dir = os.path.join(video_dir, "ADJUSTED")
    
    headvals = data['1']['streams']['HEAD']['samples']
    headlen = len(headvals)
    headi = 1
    world_lock_headval = headvals[0]['value']

    rpyvals = data['1']['streams']['RPYD']['samples']
    rpylen = len(rpyvals)
    rpyi = 0

    frame_interval = 1000/frame_rate
    framei = 0
    frame_time = 0

    if os.path.exists(work_dir) :
        shutil.rmtree(work_dir)
    os.mkdir(work_dir)

    adjust_roll = False
    adjust_pitch = False
    adjust_yaw = False

    if "level_roll" in mode :
        adjust_roll = True
    if "level_pitch" in mode :
        adjust_pitch = True
    if "unworldlock" in mode :
        adjust_yaw = True

    for frame in frames:
        options = []

        if adjust_roll or adjust_pitch :
            while frame_time > rpyvals[rpyi]['cts'] and rpyi != (rpylen - 1) :
                rpyi += 1

            if adjust_roll :
                value_roll = rpyvals[rpyi]['value'][0]
                options.append("roll=%f" % (value_roll))

            if adjust_pitch :
                value_pitch = rpyvals[rpyi]['value'][1] * -1.0
                options.append("pitch=%f" % (value_pitch))
        
        if adjust_yaw :
            if framei == 0 :
                shutil.copy(os.path.join(extract_dir,frame), os.path.join(work_dir,frame))
                frame_time += frame_interval
                framei += 1
                continue

            while frame_time > headvals[headi-1]['cts'] and headi != (headlen - 1) :
                headi += 1

            headval = headvals[headi]['value']
            # calculate the yaw adjustment needed using the calculation true heading - World Lock heading
            d_headval = headval - world_lock_headval
            if d_headval > 180 :
                d_headval -= 360
            elif d_headval < -180 :
                d_headval += 360
            
            options.append("yaw=%f" % (d_headval))

        frame_path = os.path.join(extract_dir,frame)
        out_path = os.path.join(work_dir,frame)

        options = ":".join(options)

        print("Processing frame #%d" % (framei), options)

        # use ffmpeg
        os.system("ffmpeg -i %s -hide_banner -loglevel error -vf v360=input=e:e:%s %s" % (frame_path, options, out_path))

        frame_time += frame_interval
        framei += 1

    outframes = [f for f in os.listdir(work_dir)]
    work_dir = os.path.abspath(work_dir)
    f = open('images.txt', 'w')

    for frame in outframes:
        f.write("file '%s'\n" % os.path.join(work_dir, frame))
    f.close()

    out_filename = video_filename.split(".")
    out_filename.insert(-1, f"-{mode}")
    out_filename.pop()
    out_file = os.path.join(video_dir, "%s.mp4"%(''.join(out_filename)))
    os.system(f'ffmpeg -y -r {frame_rate_str} -f concat -safe 0 -i images.txt -c:v libx264 -vf "fps={frame_rate_str},format=yuv420p" {out_file}')

    os.remove('images.txt')
    shutil.rmtree(work_dir)
    shutil.rmtree(extract_dir)