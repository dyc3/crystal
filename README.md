# Crystal

Crystal is my custom virtual assistant, tailor made for my setup.

# Features

- Modularity
- Hotword detection
- Semi-Listening mode so you don't have to keep saying the hotword
- Can roughly differentiate between commands that were intended for Crystal, and sentences that happen to contain the word "crystal"
- Deep integration with i3wm
- Cool Star Trek sound effects

These are examples of queries that Crystal can respond to accurately. For a more complete list, browse the unit tests.

## Date and Time

- What is the date?
- What is the time?
- What is tomorrow's date?
- Is tomorrow monday?
- Was yesterday friday?
- How many days until monday?

## Hardware Info

- How many processors are available?
- How many CPU threads do I have?
- How many physical cores are in the system?
- How much memory is available?
- How much disk space is available?
- Show me all storage disks.
- How much battery is left?

## Human Input

*Not a great user experience...*

- Left click.
- Type deuteranopia.
- Scroll up.
- Move the mouse 20 pixels to the left.
- Move the mouse right by 40.

## Language

- How do you spell dystopia?
- Define deuteranopia.

## Program Launching

- open spotify

## Media Control

- Pause the music.
- Toggle shuffling.
- Skip this song.
- Set volume to 50%.
- Turn it up by 30%.

## Window Manager Manipulation

- Show me desktop 5.
- Switch to workspace 3.
- Show me firefox.
- Close this.
- Kill calculator.
- Toggle floating.
- Toggle fullscreen.
- Put this on workspace 2.
- Move this workspace up.
- Move this workspace to the primary display.

## Smart Home

- Turn on the lamp
- Turn off the room light
- Toggle Paul's lights
- Scan for new devices

# Design

There are 3 types of modules:
* Input
* Action
* Feedback

The input-action pipeline looks like this:
```
+-------------+                          +------------+
|    Input    |  =>  Classification  =>  |   Action   |
+-------------+                          +------------+

[NOTE: Feedback modules can be triggered anywhere along the pipeline.]
```

### Input modules

These modules will handle the user's input, and output text only. Input modules should
apply any post processing necessary to make it easier to extract the user's intent.
There should be multiple input modules to handle speech recognition from various
services, and text input. Most use cases will only require one input module to be
used at a time.

The text output of the input module will then be classified, and sent to the matching action.

### Action modules

Actions should be relatively small modules dedicated to handling one type of command (for
example, telling the date and time).

The action should respond to the user's query and perform appropriate actions.
If no additional information is required, and the action was successful,
then Crystal returns to idle and awaits new input.

Sometimes, however, an action might require more information. The action can query the user
to specify missing or unclear parameters. The action will remember it's state and notifies
the system to prompt the user.

### Feedback modules

Feedback modules are integrations with other software to provide sensory feedback to
the user (status indicators, etc). Feedback modules can attach themselves anywhere in
the input-action pipeline.

# Setup

Here are notes for setting Crystal up on a new system (in no particular order).

## Dependencies

*Not necessarily a complete list.*

Requires Python >= 3.6

### Ubuntu >= 16.04

```bash
apt install python-dev libusb-1.0-0-dev libudev-dev flac
```

### Python packages

Everything should be in the `requirements.txt`, so
```
pip3 install -r requirements.txt
```

In order to run spacy on the gpu, the python package `thinc_gpu_ops` is required.
```
pip3 install thinc_gpu_ops
```

## Other

Snowboy must be compiled for the version of python that is being used.

blink1 can't be seen without root, UNLESS proper udev rules is set up.
blink1 udev rules go in file `/etc/udev/rules.d/51-blink1.rules`:
```
SUBSYSTEM=="input", GROUP="input", MODE="0666"
SUBSYSTEM=="usb", ATTRS{idVendor}=="27b8", ATTRS{idProduct}=="01ed", MODE:="666", GROUP="plugdev"
KERNEL=="hidraw*", ATTRS{idVendor}=="27b8", ATTRS{idProduct}=="01ed", MODE="0666", GROUP="plugdev"
```
Reload udev with `sudo udevadm control --reload-rules`. You may need to unplug/replug the device for rules to take effect.
