import os
import mpy_cross  # pip install mpy-cross

port = 'COM5'
fw = 'esp32-idf3-20191220-v1.12.bin'

files = [
    './www',
    './aws',
    './sprinkler_config.json',
    './network.json',
    './mqtt.json',
    './awsClient.py',
    './ds3231_port.py',
    './event.py',
    './microWebSrv.py',
    './ssd1306.py',
    './workScheduler.py',
    './rotary.py',
    './rtcTime.py',
    './zoneScheduler.py',
    './server.py',
    './shiftR.py',
    './sprinklerConfiguration.py',
    './ui.py',
    './wifiConnect.py',
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


print_with_header('Erase Flash (Press "Boot" button to connect)')
exec_cmd('esptool.py --chip esp32 --port {} erase_flash'.format(port))

print_with_header('Write Firmware')
exec_cmd('esptool.py --chip esp32 --port {} --baud 460800 write_flash -z 0x1000 {}'.format(port, fw))

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
        exec_cmd('ampy --port {} put "{}"'.format(port, f))
    if f.endswith('.mpy'):
        os.remove(f)

print_with_header('Done')
