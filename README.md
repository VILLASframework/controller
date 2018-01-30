# <img src="doc/pictures/villas_controller.png" width=40 /> VILLAScontroller

This project provides a unified API for controller real-time simulators from RTDS, OPAL, NI, Typhoon.

## Note

This project is currently under active development and not functionional yet!

## Quick Start

1. Install VILLAScontroller

```bash
sudo python3 setup.py install
```

2. Start RabbitMQ broker

```bash
$ docker run -p 5672:5672 -p 15672:15672 -d rabbitmq:management
```

3. Create configuration file: `config.json`:

```json
{
	"broker" : {
		"url" : "amqp://guest:guest@localhost/%2F"
	},
	"directories" : {
		"results" : "/var/lib/villas/results",
		"models" : "/var/lib/villas/models"
	},
	"simulators" : [
		{
			"name" : "Dummy Simulator #1",
			"type" : "dummy",
			"realm" : "de.rwth-aachen.eonerc.acs",
			"uuid" : "e15f5ad4-041f-11e8-9bf3-23372608bf60",
			"location" : "Steffen's Laptop",
			"owner" : "svo"
		},
		{
			"name" : "Dummy Simulator #2",
			"type" : "dummy",
			"realm" : "de.rwth-aachen.eonerc.acs",
			"uuid" : "ef6f6e46-044e-11e8-812f-17b6617a2f37",
			"location" : "Markus' Laptop",
			"owner" : "mgr"
		}
	]
}
```

4. Start VILLAScontroller daemon:

```bash
$ villas-ctl --config config.json daemon
```

5. Start monitor:

```bash
$ villas-ctl monitor
```

**Note:** If you have `jq` installed, you might want to add `| jq .` to the end for pretty printing the JSON messages.

5. Discover / ping simulators:

```bash
$ villas-ctl simulator ping
```

6. Send commands to VILLAScontroller daemon:

**Note:** Take the UUID from step 5.

```bash
$ villas-ctl simulator --uuid ef6f6e46-044e-11e8-812f-17b6617a2f37 start
$ villas-ctl simulator --uuid ef6f6e46-044e-11e8-812f-17b6617a2f37 pause
$ villas-ctl simulator --uuid ef6f6e46-044e-11e8-812f-17b6617a2f37 resume
$ villas-ctl simulator --uuid ef6f6e46-044e-11e8-812f-17b6617a2f37 stop
```

## Copyright

2017, Institute for Automation of Complex Power Systems, EONERC

## License

This project is released under the terms of the [GPL version 3](COPYING.md).

```
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
```

For other licensing options please consult [Prof. Antonello Monti](mailto:amonti@eonerc.rwth-aachen.de).

## Contact

[![EONERC ACS Logo](doc/pictures/eonerc_logo.png)](http://www.acs.eonerc.rwth-aachen.de)

 - Steffen Vogel <stvogel@eonerc.rwth-aachen.de>

[Institute for Automation of Complex Power Systems (ACS)](http://www.acs.eonerc.rwth-aachen.de)
[EON Energy Research Center (EONERC)](http://www.eonerc.rwth-aachen.de)
[RWTH University Aachen, Germany](http://www.rwth-aachen.de)
