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

# Installation

Proper installation involves setting up a service in systemd. Installation is currently
not automated and must be done manually.

Create a file `crystal.service` in `/etc/systemd/system` with the contents:

```
[Unit]
Description=Crystal
After=network.target

[Service]
Type=simple
User=carson
WorkingDirectory=/home/carson/Documents/code/crystal
PIDFile=/var/run/crystal.pid
ExecStart=/home/carson/Documents/code/crystal/crystal.sh
Restart=on-failure
StandardOutput=syslog
StandardError=syslog

[Install]
WantedBy=multi-user.target
```