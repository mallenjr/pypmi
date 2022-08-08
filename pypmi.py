import math
import sys
import os
import shutil
import re
import time

env_file = '.env'
target_temp = 40
max_temp = 80
fan_speeds = ['0x04', '0x06', '0x08', '0x0A', '0x0C', '0x0E', '0x10', '0x12', '0x14', '0x16', '0x18', '0x1A', '0x1C', '0x1E', '0x20', '0x22', '0x24', '0x26', '0x28']

def import_env():
    env_vars = {}
    required_params = {'HOST', 'USER', 'PASSWORD', 'IEK'}
    with open(env_file) as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            try:
                key, value = line.strip().split('=', 1)
                env_vars[key] = value
                required_params.remove(key)
            except:
                print('Failed to parse env file')
                sys.exit(1)

    if len(required_params) > 0:
        print(f"Missing required parameter: {list(required_params)[0]}")
        sys.exit(1)
    
    return env_vars

def ipmi_base(env_vars):
    return f"""\
        ipmitool -I lanplus -H \
        \"{env_vars['HOST']}\"\
        -U \"{env_vars['USER']}\"\
        -P \"{env_vars['PASSWORD']}\""""

def get_temps(base_command):
    output = os.popen(base_command + " sdr type temperature")
    temps = re.findall(r"\s([0-9]+)\sd", output.read())
    return list(map(lambda x: int(x), temps))

def get_fan_speed(temp):
    interval = (max_temp - target_temp) / 19
    if temp <= target_temp:
        return fan_speeds[0]

    delta = temp - target_temp
    speed_index = min(math.ceil(delta / interval), 18)
    return fan_speeds[speed_index]

def set_fan_speed(base_command, fan_speed):
    output = os.system(base_command + " raw 0x30 0x30 0x01 0x00")
    if output != 0:
        print('Failed to reset fan controller')
        sys.exit(1)
    output = os.system(base_command + f" raw 0x30 0x30 0x02 0xff {fan_speed}")
    if output != 0:
        print('Failed to set fan speed')
        sys.exit(1)

if __name__ == '__main__':
    if shutil.which("ipmitool") == None:
        print(f"Please install ipmitool")
        sys.exit(1)

    if max_temp < target_temp:
        print(f"Invalid temp configuration")
        sys.exit(1)
    
    env_vars = import_env()
    base_command = ipmi_base(env_vars)
    while (True):
        time.sleep(0.5)
        temps = get_temps(base_command)
        highest_temp = max(temps)
        print(f"Current highest temp: {highest_temp}")
        fan_speed = get_fan_speed(highest_temp)
        print(f"Setting fan speed to: {fan_speed}")
        set_fan_speed(base_command, fan_speed)