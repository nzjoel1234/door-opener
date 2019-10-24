import os

port = 'COM5'
fw = 'esp32-20190529-v1.11.bin'

files = ['www',
         'ds3231_port.py',
         'workScheduler.py',
         'microWebSrv.py',
         'rotary.py',
         'rtc_time.py',
         'scheduler.py',
         'server.py',
         'shiftR.py',
         'sprinklerConfiguration.py',
         'ssd1306.py',
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
    exec_cmd('ampy --port {} put "{}"'.format(port, f))

print_with_header('Done')
