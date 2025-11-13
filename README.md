# forhead

rasberry pi 3b powered facial tracking via active rotation


## Authors

- [@ttcdm](https://github.com/ttcdm)
- [@braydenleung-Git](https://github.com/braydenleung-Git)
- [@matthewxiaa](https://github.com/matthewxiaa)


## Step by Step Guide to reproduce

**Step 1**
log on to ras pi either via ssh or VNC or remote desktop solution(i.e [Raspberry Pi Connect](https://www.raspberrypi.com/software/connect/)) or directly

Raspberry Pi Connect or Remote Desktop:
- (setup anything that is necessary for this to work)
- connect to Raspberry Pi via "screen sharing"
- *p.s : just remote into the Raspberry Pi like it is a computer* 

ssh :
- assuming RasPi is connect to your local network or vpn correctly, and have ssh enabled enter the following command
```bash
  ssh [raspi's name]@[local ip address]
```
i.e: 
```bash
  ssh myPi@192.168.0.1
```
- you can get the ip address by typing the following command to the console
```bash
  hostname -I
```
- or go to the advance network settings of the raspberrypi, and get the ip address
- note: it is **not** the one that is IPV4, IPV6, or subnet mask
- allow finger printing, and enter the login password of your Pi

VNC : 
- assuming you have the ip address to the Raspberry Pi, and enabled vnc on Raspberry Pi
- connect to Raspberry Pi via that ip address, and enter the login password, if you have setup nothing, check out the default password for the Raspberry Pi, or consider praying you saved the password on some notebook or paper or a password manager. *(at this point, just wipe the old password via directly connecting to it, or consider wiping the SD card if you are really desperate)*

Directly: 
- plug in your display, keyboard and mouse
- power on your Raspberry Pi

**Step 2**
Download and configure python virtual environments
```bash
  git clone https://github.com/Utilities-Shared-2/forhead
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
```

**Step 3** 
Setup the electrical circuit
- data cable from the servo(we used 37kg torque, 270 deg servo in our system, please modify the code to adapt to your version of servos) are connected to the pi via pin :
    - swivle base : 11
    - tilt : 13 
- connect the servos to external power source, please make sure the following :
    - all ground are shared(including ras pi)
    - power source is adaqute
- connect the camera via USB port on the ras pi

**Step 4**
Activate the python script 
```bash
  python3 src/main.py
```





    
## Trouble Shooting

I would like to start this section by saying, this is a software as is, meaning we are not going to provide support to it, and only doing out of the kindness of our hearts. 
if non of the trouble shoot is working

I'd recommend Gemini, ChatGPT, or Perplexity/Comet, or any flavors of Ai

---

**python3 seems to be not working**
- replace python3 with the following
```bash 
    python
``` 
- if it still doesn't work, make sure you googled how to install python on your Raspberry Pi

**How to get dutycycles**
- TL:DR dutycycles is the length of the (signal/maxium pulse width) * 100
- maxium pulse width is usually 20ms, while for reference our servos 270 deg is 2.5ms
- our code uses pigpio, meaning instead of using dutycycles, it uses the pulse width to control
- there should be a short elaboration in the code, representing which part of the math is what.
- if you are into learning more, seriously, consider GPT, googling will not help as much.

## Acknowledgements
- This project would not have success without the vast online community, chat bot(yes, im serious), and our endurance to only use Ai for the last moments.
  
-[pinout for rasPi](https://pinout.xyz/)

-[Readme Editor](https://readme.so/editor)
