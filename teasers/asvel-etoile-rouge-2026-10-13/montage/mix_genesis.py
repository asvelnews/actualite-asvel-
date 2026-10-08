"""Replace the provisional score with the supplied track (Justice - Genesis), keeping the separate SFX stem.
usage: python3 mix_genesis.py genesis.mp3 trailer_video.mp4 out.mp4 [track_time_at_actions=40.0]
The track enters on the zero (trailer 5.0 s) at a contained level, rises from the first action (10.0 s) where
track time = TRACK_AT_ACTIONS, cuts for 0.4 s at 42.93 s, comes back on the last basket, fades out at the end."""
import sys, subprocess
song, video, out = sys.argv[1:4]
T = float(sys.argv[4]) if len(sys.argv) > 4 else 40.0
start = T - 5.0                     # track time playing at trailer 5.0 s
vol = ("volume='if(lt(t,5.0),0, if(lt(t,10),0.45, if(between(t,42.93,43.33),0, if(lt(t,46.63),1.0,0.85))))':eval=frame")
fc = (f"[1:a]atrim=start={start},asetpts=PTS-STARTPTS,adelay=5000|5000,{vol},afade=t=out:st=52.9:d=0.7[m];"
      "[2:a]volume=1.0[s];[m][s]amix=inputs=2:normalize=0,alimiter=limit=0.70:level=disabled[a]")
subprocess.run(['ffmpeg', '-y', '-i', video, '-i', song, '-i', 'aud/sfx.wav', '-filter_complex', fc,
                '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-shortest', out], check=True)
