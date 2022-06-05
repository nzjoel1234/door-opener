# pip install mpy-cross
# pip install adafruit-ampy
# pip install esptool

import os
import mpy_cross

port = 'COM5'
fw = 'esp32-idf3-20191220-v1.12.bin'

files = [
    './www',
    './aws',
    './ap.json',
    './wifi.json',
    './mqtt.json',
    './awsClient.py',
    './doorController.py',
    './doorSensor.py',
    './event.py',
    './microWebSrv.py',
    './networkHelper.py',
    './networkTime.py',
    './workScheduler.py',
    './server.py',
    # put boot last - don't want board to try boot with files missing
    'boot.py'
]


def print_with_header(text):
    print('****************')
    print(text)
    print('****************')


def exec_cmd(cmd):
    print('*** Exec: {}'.format(cmd))
    os.system(cmd)


skip_firmware = False

if not skip_firmware:
    print_with_header('Erase Flash (Press "Boot" button to connect)')
    exec_cmd(
        'esptool.py --chip esp32 --port {} erase_flash'.format(port))

    print_with_header('Write Firmware')
    exec_cmd(
        'esptool.py --chip esp32 --port {} --baud 460800 write_flash -z 0x1000 {}'.format(port, fw))

print_with_header('Write Application Files')
for f in files:
    if f != 'boot.py' and f.endswith('.py'):
        print('*** Precompiling: {}'.format(f))
        mpy_return_code = mpy_cross.run(f).wait(2000)
        if mpy_return_code != 0:
            print('!!! Unexpected return code: {}'.format(mpy_return_code))
        f = f.replace('.py', '.mpy')
    if not os.path.exists(f):
        print('!!! path does not exist: {}'.format(f))
    else:
        exec_cmd('ampy --delay 1 --port {} put "{}"'.format(port, f))
    if f.endswith('.mpy'):
        os.remove(f)

print_with_header('Done')
