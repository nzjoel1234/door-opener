import os
import mpy_cross  # pip install mpy-cross

port = 'COM5'
fw = 'esp32-idf3-20191220-v1.12.bin'

files = ['www',
         'uasyncio',
         'ds3231_port.mpy',
         'microWebSrv.mpy',
         'mqqt_as.mpy',
         'ssd1306.mpy',
         'mqqt_client.py',
         'workScheduler.py',
         'rotary.py',
         'rtc_time.py',
         'scheduler.py',
         'server.py',
         'shiftR.py',
         'sprinklerConfiguration.py',
         'sprinkler_config.json',
         'mqtt.json',
         'ui.py',
         'wifiConnect.py',
         # put boot last - don't want board to try boot with files missing
         'boot.py']


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
    if f.endswith('.mpy'):
        print('*** Precompiling: {}'.format(f))
        mpy_cross.run(f.replace('.mpy', '.py'))
    exec_cmd('ampy --port {} put "{}"'.format(port, f))

print_with_header('Done')
