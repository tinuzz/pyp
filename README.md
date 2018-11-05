# Pyp

Pyp is a simple data pipeline processor, written in Python3. "Pyp" means "pipe"
in Afrikaans.

Status: alpha. Work in progress.

Pyp is plugin-based, and it works like this:
* A pipeline consists of one input plugin, one or more decoder plugins and one
  or more output plugins.
* The input and decoder plugins are called in sequence and the output of each
  one is given to the next one.
* The output of the last decoder is given to *all* the output plugins.

One limitation of this model is, that you cannot create *tees* (multiple
parallel decoder/output pipelines from one input). By writing clever decoders
and output plugins, this limitation can mostly be worked around.

Here are some examples what Pyp could be used for:
* Storing output from sensors in a database, for example in a home automation
  project.
* Logging data from network traffic in a logfile and/or a database.
* Scraping websites and storing extracted data somewhere.

Pyp is a simple program, that doesn't make any assumptions about the data it
processes (though its plugins usually do!). It can be used in batch mode (ETL
of bounded data sets) and in streaming mode (continuous processing of unbounded
data). Pyp can be used in places where a *real* data pipeline like [Apache
Flink](https://flink.apache.org/) is overkill.

Pyp was created with a special use case in mind: the processing of telemetry
data from a SolarEdge solar power inverter. More information about that can be
found below.

Pyp itself has no external Python dependencies, but plugins may!

## Input plugins

An input plugin can be anything you can read data from. The following examples
already have some sort of implementation:

* *fileread* - reads from a file, optionally waiting for new data at EOF.
* *sniffer* - a packet sniffer that listens for TCP or UDP packets directed at
  one or more ports on a network interface (like a lightweight *tcpdump*)
* *tshark* - starts a [tshark](https://www.wireshark.org/docs/man-pages/tshark.html)
  process in the background and reads its stdout.
* *listen* - opens a TCP listener and reads data from client connections.

The input plugin is the heart of the program. After everything is initialized,
Pyp starts the input plugin by calling a method on its main class, and when it
returns, Pyp terminates. This means that the input plugin controls how much
data is processed. An input plugin can read data from the network in an
infinite loop and never finish, or it can read data from a file until the end
of the file and terminate when it is done. It's up to you.

## Decoder plugins

A decoder plugin takes data from an input plugin or another decoder, transforms
the data to a different form and returns it.

## Output plugins

An output plugin takes data from a decoder plugin and writes it to an output.

An output can be anything you can write data to, like for example:
* write the data to a file in JSON or some other format
* enter the data into a database, like MySQL, PostgreSQL, InfluxDB or Redis
* post the data to a webservice
* send the data over the network with the protocol of your choice, for example
  MQTT

Currently, the only implemented generic output plugins are a pretty printer
called *print* and a file writer called *datafile*. Output plugins are usually
not data-agnostic. I mean, for an output plugin to be able to write to an SQL
database, you would likely have to create a schema and write data-specific SQL
queries.

## Pipeline and data

There are no restrictions on the format of the data in any place in the
pipeline, other than that each plugin must be able to handle the data that is
is given from upstream. Most input plugins will produce either text or binary
data, so the first decoder must know what to do with it.

For example, some plugins (like *tshark* in some configurations) produce
[hexlify](https://docs.python.org/3/library/binascii.html#binascii.b2a_hex)'d
binary data, so a good choice as the first decoder in the chain would
be '*unhexlify*'. It returns pure binary data for the next decoder to process.

Where appropriate, I would recommend to make decoders return Python
dictionaries with serializeable data (str, int, float, bool, None) as values.
Dictionaries are easy to process. For example, the *print* output plugin prints
the result of `json.dumps(data)`, and you can easily create plugins that deal
with a subset of the data (a single key instead of the whole dictionary). Then
again, this is in no way a restiction of Pyp itself. Just make sure the data is
suitable for your output channel, that's all.

# Implementation details

When Pyp starts, it runs the following sequence, which I hope is self-explanatory:

```
def run(self):
    self.process_options()
    self.read_configfile()
    self.setup_logging()
    self.create_plugins()
    self.input.run()
```

* Command line options can be used to change certain parameters, the most
  important one being the location of the configuration file. But Pyp can be
  used without a configuration file, with all plugin options on the command line,
  if you like.
* The ini-style configuration file contains configuration for the main program
  and all the plugins. This is where the pipeline is defined. This can look,
  for example, like this:

```
[plugins]
input = sniffer
decode = solaredge.decode
output = print,datafile

[sniffer]
interface = vlan11

[solaredge.decode]
privkey = 12345678901234567890123456789012
```

For each defined plugin, Pyp tries to do the following:
1. Import a Python module with the name of the plugin from the *plugins*
   directory.
2. Within the module, locate a class with the same name, but capitalized
   (module *fileread* -> class *Fileread*).
3. Instantiate the class, passing its configuration, and store the instance for
   later use.

Each plugin is supposed to be a subclass of *plugins.pluginbase.Pluginbase*. This
doesn't do much, except set class attributes from the plugin configuration,
setup a logger and call an initialization method on the plugin if present.

The input plugin is passed a callback function, that it is supposed to call for
each chunk of data it wants to send into the pipeline. It takes a single
argument: the data. The callback function then takes care of calling the
decoders and output plugins. As an illustration, the simplest input plugin
*run()* method that I can think of is this:

```
    def run(self):
        with open(self.filename) as f:
            for line in f:
                self.callback(line.rstrip())
```

Plugins are instantiated only once for the lifetime of the Pyp process, which
means you can use them to temporarily hold intermediate data. That can be
convenient, if you need to buffer a certain amount of data before processing
it.

# Use case: SolarEdge telemetry data

This project was started with a specific use case in mind: the processing and
storage of telemetry data from a SolarEdge solar power inverter. In a standard
setup, SolarEdge inverters periodically send data about the state and
performance of the installation to a server operated by SolarEdge. It uses a
proprietary protocol over a TCP connection for this. Fortunately, each
*message* from the inverter is self-contained, so there is no need for any
intermediate buffering.

If you want to capture this data and store it yourself, there are a few ways
to accomplish this:

* Read the data directly from the inverter over a serial connection.
* Make the inverter talk to your own server instead of SolarEdge's server.
* Sniff the communication between the inverter and the server, and process the
  data.

So the first step is to read the data from one of these sources. For this, an
appropriate input plugin is needed. By far the easiest method to get the data,
is to sniff it from the network. Pyp comes with a simple network sniffer, that
captures all traffic on a specified network interface and passes the data from
certain packets (protocols and ports configurable) into the pipeline. In my
test setup, this works quite reliably. There is also an input plugin called
'*tshark*', that uses Tshark/Wireshark to do the capturing, optionally writing
all captured data to a [pcap](https://en.wikipedia.org/wiki/Pcap) file,
and returns the data from the packets as a Python bytearray.

Regardless of which input plugin is used, the binary data is fed into the
*solaredge* decoder plugin. This plugin is now a wrapper around the
[Python-solaredge (or pysolaredge) library](https://github.com/tinuzz/python-solaredge).

The library is mostly written by me, but a lot of ideas and code were borrowed
from other people. The data from the inverter is usually encrypted and the data
format itself is fairly complex. Most of the code that does the hard work of
decrypting and decoding the messages was copied and adapted from
[Joe Buehl's solaredge project](https://github.com/jbuehl/solaredge).
The protocol and the encryption were
[reverse-engineered](https://github.com/jbuehl/solaredge/issues/8) by a number
of contributers over a period of a few months. Pyp would never have seen the
light of day, if it wasn't for their exceptional work.

The *solaredge* plugin finally returns a Python dictionary containing
decoded telemetry data, to be handed to one or more output plugins. At this
time, the available output plugins are '*print*', '*datafile*' and '*solaredge_peewee*'.

The first two are mostly data-agnostic. '*print*' uses
[pprint](https://docs.python.org/3/library/pprint.html) to pretty-print the
data to STDOUT; '*datafile*' appends a JSON representation of the data to a
file (hence the recommendation above, to only use serializeable data types in
plugins). Neither are extremely useful, I must admit.

The third plugin, '*solaredge_peewee*', is a little more useful.
[Peewee](http://docs.peewee-orm.com/en/latest/) is a ORM that supports MySQL,
PostgreSQL and SQLite. Pysolaredge includes a module that implements
[Peewee model classes](http://docs.peewee-orm.com/en/latest/peewee/quickstart.html#model-definition)
for the SolarEdge data types 'Inverter', 'Optimizer' and 'Event'. The
'*solaredge_peewee*' output plugin uses this model to populate a MySQL or
PostgreSQL database with data from the '*solaredge*' decoder plugin.

Personally, I would prefer to store the data in a time series database (TSDB) like
[InfluxDB](https://www.influxdata.com/), which integrates nicely with tools like
[Grafana](https://grafana.com/), but an InfluxDB output plugin has yet to be written.

More information about the decoding of SolarEdge data is available in the
Github repo of [Python-solaredge](https://github.com/tinuzz/python-solaredge).

# Learn by example

## Reading and printing a file

The following example can be run in the root directory of the Pyp repository
and demonstrates the most basic usage of Pyp:

```
./run_pyp -v -d -O logfile= -O fileread.filename=/etc/passwd
```

What this means and does is:

* Run the Pyp application with verbose output (`-v` = logging to stderr)
* Set the log level to 'debug' (`-d`)
* Do not load a config file (no `-c`), so rely on built-in defaults
* The default plugins are 'fileread' for input, 'noop' for decode and 'print'
  for output
* Do not write to a logfile (`-O logfile=`), because we already have `-v`
* Tell *fileread* to read `/etc/passwd`
* The *noop* plugin will do nothing except wrap the data in a dict like so: `{
  'data': data }`
* The *print* plugin will print both the raw data and the decoded data as JSON
  to stdout

When you run this, quite a lot of output will appear on your screen:

* Log messages on stderr
* Raw input data and decoded data on stdout

If you would like to see only the decoded data, leave out `-v` (which obsoletes
`-d` when there is no logfile) and tell *print* not to print raw data:

```
./run_pyp -O logfile= -O fileread.filename=/etc/passwd -O print.print_raw=no
```

You will see each line from your *passwd* file, but wrapped as data by the *noop*
plugin.

TIP: if you run it with `-v`, you will find messages in the output containing the
words '*Setting attribute:*'. Together, these lines represent all the different
options that can be set for the pipeline you have configured.

## Sniffing DNS packets and printing the data in hexadecimal form

Again, this is not a very useful example, but it illustrates another possible
way to use Pyp. In contrast with the previous example, which processed a file
and terminated, this example will keep running until you interrupt it.

```
sudo ./run_pyp -v -d -O logfile= -O plugins.input=sniffer \
  -O sniffer.interface=eth1 -O sniffer.protocols=tcp,udp -O sniffer.ports=53 \
  -O plugins.decode=hexlify,noop -O print.print_raw=no
```

Explanation:
* Run Pyp with sudo, because the type of network socket that *sniffer* wants to
  open requires root
* Again, log to stderr (`-v`) on debug level (`-d`) and don't use a logfile
  (`-O logfile=`)
* Set the input plugin to *sniffer* (`-O plugins.input=sniffer`)
* Configure the sniffer for both UDP and TCP port 53 on interface `eth1` (the
  `-O sniffer.xxx` options)
* Set the decoders to *hexlify* and *noop*. This means that the raw binary data
  from *sniffer* will first be passed to *hexlify*, which will just call
  [binascii.hexlify()](https://docs.python.org/3/library/binascii.html#binascii.hexlify)
  on the data, and the result will be passwd to *noop*, which will wrap the
  hexlify'd data in a dictionary.
* Tell the *print* plugin not to print raw data.

The result will be, apart from the debugging output, the printing of information like this:

```
{"data": "ef5f01000001000000000000037777770977696b697065646961036f72670000010001"}

```

which is just what we asked for: a hexadecimal string representation of the
data from DNS packets, wrapped in a JSON object. Should you decide to decode
the data I quoted here, you will find it is a DNS request for the A record of
*www.wikipedia.org*.

Homework assignment: write a decode plugin to get the requested hostname
(QNAME) from the DNS Question Section. Also, write an output plugin to do
something meaningful with it ;-)

# Configuration files

Pyp can be configured entirely on the command line (with `-O` options), or you
can use a configuration file. Configuration files are ini-files and Pyp parses
them with [the configparser module](https://docs.python.org/3/library/configparser.html).

Both Pyp itself and all plugins use sections in the configuration file. Pyp itself uses
two configuration sections (`[main]` and `[plugins]`), and every plugin gets the
configuration from the section that is named after the plugin.

## Configuration file example

The configuration file for the DNS sniffer pipeline example above, but with a
logfile instead of debug output on STDERR and with both the raw data and the
"decoded" data written to a file, looks like this:

```
[main]
logfile = /tmp/pyp.log
loglevel = debug

[plugins]
input = sniffer
decode = hexlify,noop
output = datafile

[sniffer]
interface = eth1
protocols = tcp,udp
ports = 53

[datafile]
raw_data_dir = /tmp
decoded_data_dir = /tmp
```

If you save this to a file named `examples/dnssniffer.ini` (like I did ;-)),
you can now run the pipeline like this:

```
sudo ./run_pyp -c examples/dnssniffer.ini
```

No output will appear on your screen, but 3 files will appear in `/tmp`:

* `pyp.log`, the log file;
* `<yyyymmddhhmmss>.raw` (the datafile plugin uses [time.strftime()](https://docs.python.org/3/library/time.html#time.strftime)
  to generate a filename) with the raw data, hexlify'd;
* `<yyyymmddhhmmss>.data`, with the same hexlify'd data, but in concatenated JSON format,
  wrapped in an object's `data` property.

To see which configuration keys are available for each plugin, you'll have to
look at the source code for now. Each plugin that is actually configurable
defines a property called 'defaults' that holds the default values for all
possible options.
