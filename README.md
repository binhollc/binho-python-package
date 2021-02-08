# Binho Python Package

With to incredible feedback and support from our customers, we've released an entirely 
rebuilt python library for Binho Nova. While we'll continue to support our previous library,
active development will only take place on this one.

Aside from taking a more ***pythonic*** approach to implementing the library, we've also introduced
a lot of structure and abstraction to make it even easier to use your Nova, including a 
command line interface and interactive shell. We've also baked numerous example scripts right 
into the library for easy reference.

The easiest way to get started is to install this library using pip:
```bash
pip install binho
```
Using Nova in your scripts is as simple as importing the library:
```python
import binho
```

Then initialize a connection to the binho device as such:
```python
# grab the first device found the system finds
binho = binhoHostAdapter()
```

When working on setups with multiple devices, you can specify the device to connect to in 
the following 3 ways:

1)  grab the device with a specific index  
        ```
        binho = binhoHostAdapter(index=0)
        ```
2) or get the device using the COM port  
        ```
        binho = binhoHostAdapter(port=targetComport)
        ```
3) or get the device using the deviceID number  
        ```
        binho = binhoHostAdapter(deviceID = targetDeviceID)
        ```

At this point it's possible to control the device as desired. Examples of common use cases 
are included in this library and are briefly discussed below. When you're done with the device, 
be sure to close out the connection with the following:
```python
binho.close()
```
That's all there is to it. The example scripts are introduced below, but it may also make sense
to review the new Command line interface as well, as it may be possible to achieve your goals 
without writing any code at all.

### Example Scripts
Take a look in the /binho/examples folder see example scripts which demonstrate how to use
this library in your own scripts to automate Nova.

__Basic Examples:__
- [Hello World LED](binho/examples/00_hello_world_led.py)
- [Digital IO and PWM](binho/examples/01_digitalio_and_pwm.py)
- [Analog IO, DAC, and ADC](binho/examples/02_analogio_dac_and_adc.py)
- [SPI Communication](binho/examples/03_spi_communication.py)
- [I2C Communication](binho/examples/04_i2c_communication.py)
- [1Wire Communication](binho/examples/05_1wire_communication.py)

__Advanced Examples:__
- [I2C EEPROM Demo](binho/examples/10_i2c_eeprom_demo.py)
- [SPI Flash Demo](binho/examples/20_spi_flash_demo.py)
- *more coming soon*

### Command Line API

The installation of this library also includes the new command line interface which makes it 
possible to perform a lot of common functions without needing to write any code. The format of 
the commands is as follows:
```bash
binho <<subcommand>> [arguments]
```

Each command has their own unique arguments, but all commands except 'info' support the following:
- `-h, --help`: prints the list of arguments
- `-v, --verbose`: display more details on the console during execution
- `-d, --device <deviceID>`: connect to the device with the provided deviceID number
- `-p, --port <commport>`: connect to the device on the provided COM port
- `-i, --index <i>`: connect to the device at index i

*Note that only one of `-d`, `-p`, or `-i` arguments can be supplied to any command.*


##### Device Management Subcommands
- __`binho info`__  
This command can be used to find all Novas connected to the PC and get their associated information
such as serial number, COM port, and firmware version. It will also indicate if a device is in
DAPLink or Bootloader mode as well.
- __`binho dfu`__  
This command can be used to automatically update device firmware or just enter Bootloader mode.

##### IO Subcommands
- __`binho gpio`__  
- __`binho dac`__  
- __`binho adc`__  
- __`binho pwm`__  

##### Protocol Subcommands
- __`binho i2c`__  
- __`binho eeprom`__  
- __`binho spi`__  
- __`binho spiflash`__  
- __`binho 1wire`__  

##### DAPLink Subommands
Binho Nova can be used to program and debug microcontrollers by operating in DAPLink mode.
- __`binho daplink`__  
Use this command to switch Nova into and out of DAPLink mode.
- __`binho flasher`__  
While in DAPLink mode, this command can be used to program bin/hex files into microcontrollers.

##### Misc. Subommands
- __`binho shell`__  
This command can be used to open up a connection to the device and begin an interactive shell.  
- __`binho custom`__  
Adding custom commands is very easy! This command is just meant as a template which can be used to create your own commands to 
extend the command line functionality for any specific tasks. You can see the implementation [here](binho/commands/binho_custom.py)

## Development
We welcome contributions to our library. Here's some brief guidance 
to get started developing with the library. 

### Installation
```bash
python3 setup.py install
```

### Building Docs
We're planning to use ReadTheDocs to host detailed library documentation
in the near future. You can build the documentation with the following command.
```bash
pip3 install .[dev]
docs\make.bat html
```
### Roadmap
We're looking forward to adding support for various common UART use-cases. Additionally, we'll
be adding in support for Atmel SWI if we find enough folks interested in that protocol. Our
development roadmap is highly determined by customer requests and feedback, so please feel
free to reach out if there's a particular feature you'd like to see added into this library.