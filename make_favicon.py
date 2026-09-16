#!/usr/bin/env python3
"""Memorria Travels favicon set (cairosvg). White airplane mark set.
favicon.png favicon-{192,96,48,32,16}.png apple-touch-icon.png"""
import cairosvg

SITE = "/home/bitcoin/Desktop/Tourist site/"

GLYPH = ("M21 16v-2l-8-5V3.5C13 2.62 12.38 2 11.5 2S10 2.62 10 3.5V9l-8 5"
         "v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z")


def tile(size, glyph=GLYPH, radius="24%", mono=False):
    if mono:
        return ("<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{0}\" "
                "height=\"{0}\" viewBox=\"0 0 512 512\">"
                "<rect width=\"512\" height=\"512\" rx=\"20%\" "
                "fill=\"#003E78\"/>"
                "<path d=\"{1}\" transform=\"translate(256 140) scale(9.8)\" "
                "fill=\"#FFFFFF\"/></svg>").format(size, glyph)
    return ("<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{0}\" "
            "height=\"{0}\" viewBox=\"0 0 512 512\">"
            "<defs><linearGradient id=\"g\" x1=\"0\" y1=\"0\" x2=\"0\" "
            "y2=\"1\"><stop offset=\"0\" stop-color=\"#0087C7\"/>"
            "<stop offset=\"0.55\" stop-color=\"#0468AE\"/>"
            "<stop offset=\"1\" stop-color=\"#003E78\"/></linearGradient>"
            "</defs>"
            "<rect x=\"16\" y=\"16\" width=\"480\" height=\"480\" rx=\"{2}\" "
            "fill=\"url(#g)\"/>"
            "<path d=\"{1}\" transform=\"translate(256 140) scale(9.8)\" "
            "fill=\"#FFFFFF\"/></svg>").format(size, glyph, radius)


def write_png(name, w, h, glyph=GLYPH, radius="24%", mono=False):
    svg = tile(max(w, h), glyph, radius, mono)
    data = cairosvg.svg2png(bytestring=svg.encode("utf-8"),
                            output_width=w, output_height=h)
    with open(SITE + name, "wb") as f:
        f.write(data)
    print("  %-24s %6d bytes" % (name, len(data)))


def main():
    write_png("favicon.png", 512, 512)
    write_png("apple-touch-icon.png", 180, 180, radius="18%")
    write_png("favicon-192.png", 192, 192)
    write_png("favicon-96.png", 96, 96)
    write_png("favicon-48.png", 48, 48, mono=True)
    write_png("favicon-32.png", 32, 32, mono=True)
    write_png("favicon-16.png", 16, 16, mono=True)
    print("favicon set regenerated")


if __name__ == "__main__":
    main()
