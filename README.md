# Crystal

## Design

**NOTE: This isn't the way it's set up now, but it's the goal.**

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

Snowboy must be compiled for the version of python that is being used.

blink1 can't be seen without root, UNLESS proper udev rules is set up.
blink1 udev rules go in file `/etc/udev/rules.d/51-blink1.rules`:
```
SUBSYSTEM=="input", GROUP="input", MODE="0666"
SUBSYSTEM=="usb", ATTRS{idVendor}=="27b8", ATTRS{idProduct}=="01ed", MODE:="666", GROUP="plugdev"
KERNEL=="hidraw*", ATTRS{idVendor}=="27b8", ATTRS{idProduct}=="01ed", MODE="0666", GROUP="plugdev"
```
Reload udev with `sudo udevadm control --reload-rules`. You may need to unplug/replug device for rules to take effect.
