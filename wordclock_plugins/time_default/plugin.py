import datetime
import logging
import os
import time
import wordclock_tools.wordclock_colors as wcc


class plugin:
    """
    A class to display the current time (default mode).
    This default mode needs to be adapted to the hardware
    layout of the wordclock (the chosen stencil) and is
    the most essential time display mode of the wordclock.
    """

    def __init__(self, config):
        """
        Initializations for the startup of the current wordclock plugin
        """
        # Get plugin name (according to the folder, it is contained in)
        self.name = os.path.dirname(__file__).split('/')[-1]
        self.pretty_name = "The time"
        self.description = "The minimum, you should expect from a wordclock."

        # typewriter effect
        try:
            self.typewriter = config.getboolean('plugin_' + self.name, 'typewriter')
        except:
            logging.warning('No typewriter-flag set for default plugin within the config-file. Typewriter animation will be used.')
            self.typewriter = True

        self.animation = "typewriter" if self.typewriter else "fadeOutIn"

        try:
            self.typewriter_speed = config.getint('plugin_' + self.name, 'typewriter_speed')
        except:
            self.typewriter_speed = 5
            logging.warning('No typewriter_speed set for default plugin within the config-file. Defaulting to ' + str(
                self.typewriter_speed) + '.')

        try:
            self.purist = config.getboolean('plugin_time_default', 'purist')
        except:
            logging.warning('No purist-flag set for default plugin within the config-file. Prefix will be displayed.')
            self.purist = False

        # sleep mode
        try:
            self.sleep_begin = datetime.datetime.strptime(config.get('plugin_' + self.name, 'sleep_begin'), '%H:%M').time()
            self.sleep_end = datetime.datetime.strptime(config.get('plugin_' + self.name, 'sleep_end'), '%H:%M').time()
        except:
            self.sleep_begin = datetime.time(0,0)
            self.sleep_end = datetime.time(0,0)
            logging.warning('  No sleeping time set, display will stay bright 24/7.')

        try:
            self.sleep_brightness = config.getint('plugin_' + self.name, 'sleep_brightness')
        except:
            self.sleep_brightness = 5
            logging.warning('  No sleep brightness set within the config-file. Defaulting to ' + str(
                self.sleep_brightness) + '.')

        # Choose default fgcolor
        try:
            fgcolor = ''.join(config.get('wordclock', 'default-fg-color'))
        except:
            # For backward compatibility
            fgcolor = ''.join(config.get('plugin_time_default', 'default-fg-color'))

        if fgcolor == 'BLACK':
            self.word_color = wcc.BLACK
            self.minute_color = wcc.BLACK
        elif fgcolor == 'WHITE':
            self.word_color = wcc.WHITE
            self.minute_color = wcc.WHITE
        elif fgcolor == 'WWHITE':
            self.word_color = wcc.WWHITE
            self.minute_color = wcc.WWHITE
        elif fgcolor == 'RED':
            self.word_color = wcc.RED
            self.minute_color = wcc.RED
        elif fgcolor == 'YELLOW':
            self.word_color = wcc.YELLOW
            self.minute_color = wcc.YELLOW
        elif fgcolor == 'LIME':
            self.word_color = wcc.LIME
            self.minute_color = wcc.LIME
        elif fgcolor == 'GREEN':
            self.word_color = wcc.GREEN
            self.minute_color = wcc.GREEN
        elif fgcolor == 'BLUE':
            self.word_color = wcc.BLUE
            self.minute_color = wcc.BLUE
        else:
            print('Could not detect default-fg-color: ' + fgcolor + '.')
            print('Choosing default: warm white')
            self.word_color = wcc.WWHITE
            self.minute_color = wcc.WWHITE

        # Choose default bgcolor
        try:
            bgcolor = ''.join(config.get('wordclock', 'default-bg-color'))
        except:
            # For backward compatibility
            bgcolor = ''.join(config.get('plugin_time_default', 'default-bg-color'))

        if bgcolor == 'BLACK':
            self.bg_color = wcc.BLACK
        elif bgcolor == 'WHITE':
            self.bg_color = wcc.WHITE
        elif bgcolor == 'WWHITE':
            self.bg_color = wcc.WWHITE
        elif bgcolor == 'RED':
            self.bg_color = wcc.RED
        elif bgcolor == 'YELLOW':
            self.bg_color = wcc.YELLOW
        elif bgcolor == 'LIME':
            self.bg_color = wcc.LIME
        elif bgcolor == 'GREEN':
            self.bg_color = wcc.GREEN
        elif bgcolor == 'BLUE':
            self.bg_color = wcc.BLUE
        else:
            print('Could not detect default-bg-color: ' + bgcolor + '.')
            print('Choosing default: black')
            self.bg_color = wcc.BLACK

        # Other color modes...
        self.color_modes = \
            [[wcc.BLACK, wcc.WWHITE, wcc.WWHITE],
             [wcc.BLACK, wcc.WHITE, wcc.WHITE],
             [wcc.BLACK, wcc.ORANGE, wcc.ORANGE],
             [wcc.BLACK, wcc.ORANGE, wcc.WWHITE],
             [wcc.BLACK, wcc.PINK, wcc.GREEN],
             [wcc.BLACK, wcc.RED, wcc.YELLOW],
             [wcc.BLACK, wcc.BLUE, wcc.RED],
             [wcc.BLACK, wcc.RED, wcc.BLUE],
             [wcc.YELLOW, wcc.RED, wcc.BLUE],
             [wcc.RED, wcc.BLUE, wcc.BLUE],
             [wcc.RED, wcc.WHITE, wcc.WHITE],
             [wcc.GREEN, wcc.YELLOW, wcc.PINK],
             [wcc.WWHITE, wcc.BLACK, wcc.BLACK],
             [wcc.BLACK, wcc.Color(30, 30, 30), wcc.Color(30, 30, 30)]]
        self.color_mode_pos = 0
        self.rb_pos = 0  # index position for "rainbow"-mode
        try:
            self.brightness_mode_pos = config.getint('wordclock_display', 'brightness')
        except:
            logging.warning("Brightness value not set in config-file: To do so, add a \"brightness\" between 1..255 to the [wordclock_display]-section.")
            self.brightness_mode_pos = 255
        self.brightness_change = 8

        try:
            self.use_brightness_sensor = config.getboolean('wordclock_display', 'use_brightness_sensor')            
        except:
            print('Not found brigtness sensor value ')
            self.use_brightness_sensor = False

        print(('Using brigtness sensor : ' + str(self.use_brightness_sensor)))
        if self.use_brightness_sensor:
            print('Importing sensor Library ')
            import Adafruit_GPIO.I2C as I2C
            address = 0x39 ## Device address
            self.i2c = I2C.Device(address,1)
        # save current brightness for switching back from sleep mode
        self.wake_brightness = self.brightness_mode_pos

    def run(self, wcd, wci):
        """
        Displays time until aborted by user interaction on pin button_return
        """
        # Some initializations of the "previous" minute
        prev_min = -1
        if self.use_brightness_sensor:
            control_on = 0x03 ## "On" value
            control_off = 0x00 ## "Off" value
            
            sensorMin = 0.0
            sensorMax = 100.0

            sensorCurrent = 120.0

            brightnessMin = 50.0
            brightnessMax = 255.0

            try:
                self.i2c.write8(0x00, control_on)
            except IOError as e:
                print(e)
            time.sleep(0.2)
            self.brightness_mode_pos = min(((((brightnessMax - brightnessMin) / sensorMax) * sensorCurrent) + brightnessMin),255)

        while True:
            # Get current time
            now = datetime.datetime.now()
            newBrightness = self.brightness_mode_pos
            if self.use_brightness_sensor:
                try:
                    sensorCurrent = float(self.i2c.readU16(0x8C))
                    #print('sensorCurrent is ' + str(sensorCurrent))
                    newBrightness = min(((((brightnessMax - brightnessMin) / sensorMax) * sensorCurrent) + brightnessMin),255)
                    newBrightness = int(newBrightness)
                except IOError as e:
                    print(e)
                time.sleep(0.2)

            # Check, if a minute has passed (to render the new time)
            if prev_min < now.minute:
                sleepActive = \
                    self.sleep_begin <= now.time() < self.sleep_end or \
                    self.sleep_end < self.sleep_begin <= now.time() <= datetime.time(23, 59, 59) or \
                    now.time() < self.sleep_end < self.sleep_begin

                wcd.setBrightness(self.sleep_brightness if sleepActive else newBrightness)
 
                # Set background color
                self.show_time(wcd, wci, animation=self.animation)
                prev_min = -1 if now.minute == 59 else now.minute

            if newBrightness != self.brightness_mode_pos:
                self.brightness_mode_pos = newBrightness
                wcd.setBrightness(newBrightness)
                self.show_time(wcd, wci, animation=self.animation)

            event = wci.waitForEvent(2)
            # Switch display color, if button_left is pressed
            if event == wci.EVENT_BUTTON_LEFT:
                self.color_mode_pos += 1
                if self.color_mode_pos == len(self.color_modes):
                    self.color_mode_pos = 0
                self.bg_color = self.color_modes[self.color_mode_pos][0]
                self.word_color = self.color_modes[self.color_mode_pos][1]
                self.minute_color = self.color_modes[self.color_mode_pos][2]
                self.show_time(wcd, wci, animation=self.animation)
                time.sleep(0.2)
            if (event == wci.EVENT_BUTTON_RETURN) \
                    or (event == wci.EVENT_EXIT_PLUGIN) \
                    or (event == wci.EVENT_NEXT_PLUGIN_REQUESTED):
                wcd.setBrightness(self.wake_brightness)
                wcd.show()
                self.skip_sleep = False
                return
            if event == wci.EVENT_BUTTON_RIGHT:
                time.sleep(wci.lock_time)
                self.color_selection(wcd, wci)

    def show_time(self, wcd, wci, animation=None):
        now = datetime.datetime.now()
        # Set background color
        wcd.setColorToAll(self.bg_color, includeMinutes=True)
        # Returns indices, which represent the current time, when being illuminated
        taw_indices = wcd.taw.get_time(now, self.purist)
        wcd.setColorBy1DCoordinates(taw_indices, self.word_color)
        wcd.setMinutes(now, self.minute_color)
        wcd.show(animation)

    def color_selection(self, wcd, wci):
        while True:
            # BEGIN: Rainbow generation as done in rpi_ws281x strandtest example! Thanks to Tony DiCola for providing :)
            if self.rb_pos < 85:
                self.word_color = self.minute_color = wcc.Color(3 * self.rb_pos, 255 - 3 * self.rb_pos, 0)
            elif self.rb_pos < 170:
                self.word_color = self.minute_color = wcc.Color(255 - 3 * (self.rb_pos - 85), 0, 3 * (self.rb_pos - 85))
            else:
                self.word_color = self.minute_color = wcc.Color(0, 3 * (self.rb_pos - 170),
                                                                255 - 3 * (self.rb_pos - 170))
            # END: Rainbow generation as done in rpi_ws281x strandtest example! Thanks to Tony DiCola for providing :)
            # TODO: Evaluate taw_indices only every n-th loop (saving resources)
            now = datetime.datetime.now()  # Set current time
            taw_indices = wcd.taw.get_time(now, self.purist)
            wcd.setColorToAll(self.bg_color, includeMinutes=True)
            wcd.setColorBy1DCoordinates(taw_indices, self.word_color)
            wcd.setMinutes(now, self.minute_color)
            wcd.show()
            self.rb_pos += 1
            if self.rb_pos == 256: self.rb_pos = 0
            event = wci.waitForEvent(0.1)
            if event != wci.EVENT_INVALID:
                time.sleep(wci.lock_time)
                break
        if not self.use_brightness_sensor:
            while True:
                self.brightness_mode_pos += self.brightness_change
                # TODO: Evaluate taw_indices only every n-th loop (saving resources)
                now = datetime.datetime.now()  # Set current time
                taw_indices = wcd.taw.get_time(now, self.purist)
                wcd.setColorToAll(self.bg_color, includeMinutes=True)
                wcd.setColorBy1DCoordinates(taw_indices, self.word_color)
                wcd.setMinutes(now, self.minute_color)
                wcd.setBrightness(self.brightness_mode_pos)
                wcd.show()
                if self.brightness_mode_pos < abs(self.brightness_change) or self.brightness_mode_pos > 255 - abs(
                        self.brightness_change):
                    self.brightness_change *= -1
                event = wci.waitForEvent(0.1)
                if event != wci.EVENT_INVALID:
                    time.sleep(wci.lock_time)
                    return
