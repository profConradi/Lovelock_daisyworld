from microbit import *
while True:
    lightLevel = display.read_light_level()
    print(lightLevel)
    sleep(100)