import badger2040
import jpegdec

MAP_IMAGE_HEIGHT = 128
MAP_IMAGE_WIDTH = 192
EQUATOR_Y = MAP_IMAGE_HEIGHT // 2
MERIDIAN_X = MAP_IMAGE_WIDTH // 2

TEXT_LEFT_OFFSET = 2
MAP_LEFT_OFFSET = badger2040.WIDTH - MAP_IMAGE_WIDTH
MAP_TOP_OFFSET = 0

display = badger2040.Badger2040()
display.set_update_speed(badger2040.UPDATE_NORMAL)
display.led(0)

def load_world_map():
    jpg = jpegdec.JPEG(display.display)
    jpg.open_file("worldmap.jpg")
    jpg.decode(MAP_LEFT_OFFSET, 0, jpegdec.JPEG_SCALE_FULL, dither=False)
    
display.clear()
load_world_map()
display.set_pen(15)
display.rectangle(0, 0, MAP_LEFT_OFFSET, badger2040.HEIGHT)

display.set_font("bitmap8")
display.set_pen(0)
display.text("88888", TEXT_LEFT_OFFSET, 2, scale=4)
display.text("miles away", TEXT_LEFT_OFFSET, 32, scale=2)
display.text("South Yunderup, Australia", TEXT_LEFT_OFFSET, 54, wordwrap=badger2040.WIDTH - MAP_IMAGE_WIDTH - TEXT_LEFT_OFFSET, scale=2)
display.text("Nov 30 14:50 UTC", TEXT_LEFT_OFFSET, 118, scale=1)


iss_lat = -32.5873782
iss_lon = 115.78379

meridian_offset_px = abs(iss_lon) * (MAP_IMAGE_WIDTH / 360)
iss_x = (round(MERIDIAN_X - meridian_offset_px if iss_lon < 0 else MERIDIAN_X + meridian_offset_px)) + MAP_LEFT_OFFSET

equator_offset_px = abs(iss_lat) * (MAP_IMAGE_HEIGHT / 180)
iss_y = (round(EQUATOR_Y - equator_offset_px if iss_lat >= 0 else EQUATOR_Y + equator_offset_px)) + MAP_TOP_OFFSET

display.circle(iss_x, iss_y, 4)

display.update()