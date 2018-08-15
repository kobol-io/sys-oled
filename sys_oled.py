#!/usr/bin/env python

import signal
import os
import sys
import time
import psutil
from datetime import datetime
from luma.core import cmdline, error
from PIL import Image, ImageDraw, ImageFont

# Define interval between image
interval = 4

font_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                'font', 'C&C Red Alert [INET].ttf'))
font = ImageFont.truetype(font_path, 12)

def get_device(actual_args=None):
    if actual_args is None:
        actual_args = sys.argv[1:]
    parser = cmdline.create_parser(description='luma.core arguments')
    args = parser.parse_args(actual_args)

    if args.config:
        config = cmdline.load_config(args.config)
        args = parser.parse_args(config + actual_args)

    try:
        device = cmdline.create_device(args)
    except error.Error as e:
        parser.error(e)

    return device

def bytes2human(n):
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = int(float(n) / prefix[s])
            return '%s%s' % (value, s)
    return "%sB" % n


def cpu_usage():
    uptime = datetime.now().replace(microsecond=0) - datetime.fromtimestamp(psutil.boot_time())
    av1, av2, av3 = os.getloadavg()
    return "ld: %.1f %.1f %.1f up: %s" \
        % (av1, av2, av3, str(uptime).split(',')[0])


def mem_usage():
    usage = psutil.virtual_memory()
    return "mem: %s / %s %.0f%%" \
        % (bytes2human(usage.used), bytes2human(usage.total), usage.percent)


def disk_usage(name, dir):
    usage = psutil.disk_usage(dir)
    return name + ": %s / %s - %.0f%%" \
        % (bytes2human(usage.used), bytes2human(usage.total), usage.percent)


def network(iface):
    addr = psutil.net_if_addrs()[iface]
    return "%s: %s" \
        % (iface, addr[0].address)

def host_time():
    now = datetime.now()
    hostname = os.uname()[1]
    return hostname + " - " + now.strftime("%Y-%m-%d %H:%M")

def status(device):
    txt = Image.new('RGBA', device.size)
    d = ImageDraw.Draw(txt)
    d.text((0, 0), cpu_usage(), font=font, fill="white")
    d.line([(0,13),(128,13)])
    d.text((0, 15), mem_usage(), font=font, fill="white")
    d.text((0, 27), disk_usage('sd', '/'), font=font, fill="white")
    d.text((0, 39), disk_usage('md0', '/'), font=font, fill="white")
    d.text((0, 51), network('eth0'), font=font, fill="white")

    device.display(txt.convert(device.mode))


def logo(device, msg):
    img_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
        'img', 'helios4_logo.png'))
    logo = Image.open(img_path).convert("RGBA")

    background = Image.new("RGBA", device.size)
    background.paste(logo, (0, 0))

    txt = Image.new('RGBA', device.size)
    d = ImageDraw.Draw(txt)
    d.text((0,52), msg, font=font, fill="white")

    out = Image.alpha_composite(background, txt)
    device.display(out.convert(device.mode))

def sigterm_handler():
    sys.exit(0)

signal.signal(signal.SIGTERM, sigterm_handler)


def main():
    if 'HELIOS4_STARTING' in os.environ:
        logo(device, "System Starting...")
        device.persist = True
	time.sleep(6)
    else:
        while True:
            status(device)
            time.sleep(interval)
	    logo(device, host_time())
            time.sleep(interval)

if __name__ == "__main__":
    try:
        device = get_device()
        main()
    except KeyboardInterrupt:
        pass
