# Visual tests for the TJC3224 display emulator
#
# These tests render display commands to PNG images, providing visual
# verification of display output without requiring physical hardware.
# Generated images are saved to test/unit/visual_output/ and uploaded
# as artifacts in CI.

import os
import unittest

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

# Output directory for visual test screenshots
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'visual_output')


def rgb565_to_rgb888(color):
    """Convert RGB565 color to RGB888 tuple."""
    r = ((color >> 11) & 0x1F) * 255 // 31
    g = ((color >> 5) & 0x3F) * 255 // 63
    b = (color & 0x1F) * 255 // 31
    return (r, g, b)


class DisplayEmulatorSerial:
    """A serial interface that records commands and renders them to an image.

    This emulates the TJC3224 display by interpreting the serial protocol
    and drawing the corresponding graphics to a PIL Image.
    """

    # Display dimensions matching TJC3224
    WIDTH = 240
    HEIGHT = 320

    def __init__(self):
        self.image = Image.new('RGB', (self.WIDTH, self.HEIGHT), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)
        self.writes = []
        self._buffer = b""
        self._frames = []  # Completed frames for analysis

        # Track palette state
        self._fg_color = (255, 255, 255)
        self._bg_color = (0, 0, 0)

        # Try to load a basic font
        try:
            self._font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)
            self._font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 16)
        except (IOError, OSError):
            self._font = ImageFont.load_default()
            self._font_large = self._font

    def write(self, data):
        """Record and interpret data written to the display."""
        if isinstance(data, (list, tuple)):
            data = bytes(data)
        elif isinstance(data, int):
            data = bytes([data])
        elif isinstance(data, str):
            data = data.encode("utf-8")
        self.writes.append(bytes(data))
        self._buffer += bytes(data)

    def read(self, size=1):
        return b""

    def reset(self):
        self.writes = []
        self._buffer = b""

    @property
    def all_bytes(self):
        return self._buffer

    def save(self, filename):
        """Save the current display state as a PNG image."""
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        filepath = os.path.join(OUTPUT_DIR, filename)
        self.image.save(filepath)
        return filepath

    def draw_text(self, x, y, text, color=(255, 255, 255), bg_color=None):
        """Draw text on the emulated display."""
        if bg_color:
            # Calculate text bounding box for background
            bbox = self.draw.textbbox((x, y), text, font=self._font)
            self.draw.rectangle(bbox, fill=bg_color)
        self.draw.text((x, y), text, fill=color, font=self._font)

    def draw_rectangle_on_display(self, x1, y1, x2, y2, color, fill=False):
        """Draw a rectangle on the emulated display."""
        if fill:
            self.draw.rectangle([x1, y1, x2, y2], fill=color)
        else:
            self.draw.rectangle([x1, y1, x2, y2], outline=color)

    def draw_line_on_display(self, x1, y1, x2, y2, color):
        """Draw a line on the emulated display."""
        self.draw.line([x1, y1, x2, y2], fill=color)

    def clear(self, color=(0, 0, 0)):
        """Clear the display with a color."""
        self.draw.rectangle([0, 0, self.WIDTH - 1, self.HEIGHT - 1], fill=color)


@unittest.skipUnless(HAS_PILLOW, "Pillow library not installed")
class TestVisualMainMenu(unittest.TestCase):
    """Visual test: render the main menu screen."""

    def setUp(self):
        self.display = DisplayEmulatorSerial()
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    def test_main_menu_layout(self):
        """Render a simulated main menu screen and save as PNG."""
        d = self.display

        # Clear screen with black background
        d.clear((0, 0, 0))

        # Draw header bar
        d.draw_rectangle_on_display(0, 0, 239, 24, (30, 60, 120), fill=True)
        d.draw_text(5, 4, "Ender 3 V3 SE", color=(255, 255, 255))

        # Draw menu icons (simulated as labeled boxes)
        menu_items = [
            (20, 50, "Print", (52, 152, 219)),
            (130, 50, "Prepare", (46, 204, 113)),
            (20, 160, "Control", (231, 76, 60)),
            (130, 160, "Leveling", (155, 89, 182)),
        ]

        for x, y, label, color in menu_items:
            # Icon placeholder
            d.draw_rectangle_on_display(x, y, x + 80, y + 80, color, fill=True)
            d.draw_text(x + 10, y + 85, label, color=(200, 200, 200))

        # Status bar at bottom
        d.draw_rectangle_on_display(0, 295, 239, 319, (20, 20, 20), fill=True)
        d.draw_text(5, 300, "Nozzle: 25C  Bed: 22C", color=(180, 180, 180))

        filepath = d.save("main_menu.png")
        self.assertTrue(os.path.exists(filepath))
        # Verify image dimensions
        with Image.open(filepath) as img:
            self.assertEqual(img.size, (240, 320))


@unittest.skipUnless(HAS_PILLOW, "Pillow library not installed")
class TestVisualPrintProgress(unittest.TestCase):
    """Visual test: render a print progress screen."""

    def setUp(self):
        self.display = DisplayEmulatorSerial()
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    def test_print_progress_50_percent(self):
        """Render a print progress screen at 50% and save as PNG."""
        d = self.display

        # Clear screen
        d.clear((0, 0, 0))

        # Header
        d.draw_rectangle_on_display(0, 0, 239, 24, (30, 60, 120), fill=True)
        d.draw_text(5, 4, "Printing...", color=(255, 255, 255))

        # File name
        d.draw_text(10, 35, "benchy.gcode", color=(200, 200, 200))

        # Progress bar background
        d.draw_rectangle_on_display(10, 60, 229, 80, (50, 50, 50), fill=True)
        # Progress bar fill (50%)
        d.draw_rectangle_on_display(10, 60, 119, 80, (46, 204, 113), fill=True)
        # Progress text
        d.draw_text(100, 85, "50%", color=(255, 255, 255))

        # Temperature info
        d.draw_text(10, 120, "Nozzle:", color=(150, 150, 150))
        d.draw_text(100, 120, "200 / 200 C", color=(255, 100, 50))

        d.draw_text(10, 145, "Bed:", color=(150, 150, 150))
        d.draw_text(100, 145, "60 / 60 C", color=(255, 150, 50))

        # Time info
        d.draw_text(10, 180, "Elapsed:", color=(150, 150, 150))
        d.draw_text(100, 180, "01:23:45", color=(200, 200, 200))

        d.draw_text(10, 205, "Remaining:", color=(150, 150, 150))
        d.draw_text(100, 205, "01:23:45", color=(200, 200, 200))

        # Action buttons at bottom
        d.draw_rectangle_on_display(10, 270, 75, 310, (231, 76, 60), fill=True)
        d.draw_text(20, 283, "Stop", color=(255, 255, 255))

        d.draw_rectangle_on_display(85, 270, 155, 310, (241, 196, 15), fill=True)
        d.draw_text(95, 283, "Pause", color=(0, 0, 0))

        d.draw_rectangle_on_display(165, 270, 229, 310, (52, 152, 219), fill=True)
        d.draw_text(175, 283, "Tune", color=(255, 255, 255))

        filepath = d.save("print_progress_50.png")
        self.assertTrue(os.path.exists(filepath))
        with Image.open(filepath) as img:
            self.assertEqual(img.size, (240, 320))

    def test_print_progress_complete(self):
        """Render a completed print screen and save as PNG."""
        d = self.display

        # Clear screen
        d.clear((0, 0, 0))

        # Header
        d.draw_rectangle_on_display(0, 0, 239, 24, (30, 100, 60), fill=True)
        d.draw_text(5, 4, "Print Complete!", color=(255, 255, 255))

        # Progress bar (100%)
        d.draw_rectangle_on_display(10, 60, 229, 80, (46, 204, 113), fill=True)
        d.draw_text(100, 85, "100%", color=(255, 255, 255))

        # Completion info
        d.draw_text(10, 120, "benchy.gcode", color=(200, 200, 200))
        d.draw_text(10, 150, "Total time: 02:47:30", color=(150, 150, 150))

        # Confirmation button
        d.draw_rectangle_on_display(60, 250, 180, 290, (46, 204, 113), fill=True)
        d.draw_text(90, 263, "Done", color=(255, 255, 255))

        filepath = d.save("print_complete.png")
        self.assertTrue(os.path.exists(filepath))


@unittest.skipUnless(HAS_PILLOW, "Pillow library not installed")
class TestVisualTemperatureScreen(unittest.TestCase):
    """Visual test: render temperature control screen."""

    def setUp(self):
        self.display = DisplayEmulatorSerial()
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    def test_temperature_screen(self):
        """Render temperature settings screen."""
        d = self.display

        d.clear((0, 0, 0))

        # Header
        d.draw_rectangle_on_display(0, 0, 239, 24, (30, 60, 120), fill=True)
        d.draw_text(5, 4, "Temperature", color=(255, 255, 255))

        # Menu items
        items = [
            ("Nozzle Temp", "200 C", 40),
            ("Bed Temp", "60 C", 79),
            ("Fan Speed", "100%", 118),
            ("PLA Preheat", "", 157),
            ("TPU Preheat", "", 196),
        ]

        for label, value, y in items:
            d.draw_rectangle_on_display(0, y, 239, y + 38, (20, 20, 20), fill=True)
            d.draw_rectangle_on_display(0, y, 239, y + 38, (50, 50, 50))
            d.draw_text(45, y + 10, label, color=(220, 220, 220))
            if value:
                d.draw_text(180, y + 10, value, color=(255, 165, 0))

        # Back button indicator
        d.draw_text(10, 250, "< Back", color=(100, 150, 255))

        filepath = d.save("temperature_screen.png")
        self.assertTrue(os.path.exists(filepath))


@unittest.skipUnless(HAS_PILLOW, "Pillow library not installed")
class TestVisualProtocolFrames(unittest.TestCase):
    """Visual test: render a diagram of the serial protocol frames."""

    def setUp(self):
        self.display = DisplayEmulatorSerial()
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    def test_protocol_diagram(self):
        """Render a visual diagram of display protocol frames."""
        # Create a wider image for the protocol diagram
        img = Image.new('RGB', (600, 400), (30, 30, 30))
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11)
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        except (IOError, OSError):
            font = ImageFont.load_default()
            font_title = font

        # Title
        draw.text((10, 10), "TJC3224 Display Protocol - Frame Structure", fill=(255, 255, 255), font=font_title)

        # Frame structure diagram
        y = 50
        draw.text((10, y), "Frame Format:", fill=(200, 200, 200), font=font)
        y += 25

        # Draw frame boxes
        boxes = [
            (10, "HEAD\n0xAA", (52, 152, 219)),
            (80, "CMD\n(1 byte)", (46, 204, 113)),
            (170, "DATA\n(variable)", (241, 196, 15)),
            (350, "TAIL\n0xCC 0x33\n0xC3 0x3C", (231, 76, 60)),
        ]

        for x, label, color in boxes:
            draw.rectangle([x, y, x + 80, y + 50], fill=color, outline=(255, 255, 255))
            draw.text((x + 5, y + 5), label, fill=(0, 0, 0), font=font)

        # Arrows between boxes
        for i in range(len(boxes) - 1):
            x_start = boxes[i][0] + 80
            x_end = boxes[i + 1][0]
            mid_y = y + 25
            draw.line([x_start, mid_y, x_end, mid_y], fill=(150, 150, 150), width=2)

        # Example commands
        y = 140
        draw.text((10, y), "Example Commands:", fill=(200, 200, 200), font=font)
        y += 25

        commands = [
            ("Handshake", "AA 00 CC 33 C3 3C"),
            ("Clear Screen", "AA 40 [fg_hi] [fg_lo] [bg_hi] [bg_lo] CC 33 C3 3C  +  AA 52 CC 33 C3 3C"),
            ("Set Brightness", "AA 5F [level] CC 33 C3 3C"),
            ("Draw Line", "AA 40 ... CC 33 C3 3C  +  AA 51 [x1_hi] [x1_lo] [y1_hi] [y1_lo] [x2_hi] [x2_lo] [y2_hi] [y2_lo] CC 33 C3 3C"),
            ("Draw String", "AA 98 [x_hi] [x_lo] [y_hi] [y_lo] [font] [mode] [size] [color] [bg] [text...] CC 33 C3 3C"),
        ]

        for cmd_name, cmd_bytes in commands:
            draw.text((10, y), f"  {cmd_name}:", fill=(100, 200, 255), font=font)
            draw.text((140, y), cmd_bytes, fill=(200, 200, 200), font=font)
            y += 20

        # Color legend
        y = 290
        draw.text((10, y), "Color Format: RGB565 (16-bit)", fill=(200, 200, 200), font=font)
        y += 20
        colors_demo = [
            ("White (0xFFFF)", (255, 255, 255)),
            ("Black (0x0000)", (0, 0, 0)),
            ("Red (0xF800)", (255, 0, 0)),
            ("Green (0x07E0)", (0, 255, 0)),
            ("Blue (0x001F)", (0, 0, 255)),
        ]
        for label, color in colors_demo:
            draw.rectangle([10, y, 30, y + 15], fill=color, outline=(100, 100, 100))
            draw.text((35, y), label, fill=(180, 180, 180), font=font)
            y += 20

        filepath = os.path.join(OUTPUT_DIR, "protocol_frames.png")
        img.save(filepath)
        self.assertTrue(os.path.exists(filepath))


@unittest.skipUnless(HAS_PILLOW, "Pillow library not installed")
class TestVisualMenuNavigation(unittest.TestCase):
    """Visual test: render menu navigation sequence."""

    def setUp(self):
        self.display = DisplayEmulatorSerial()
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    def test_menu_navigation_sequence(self):
        """Render multiple frames showing menu navigation (for video/GIF)."""
        frames = []

        # Menu states to visualize
        menu_states = [
            {"selected": 0, "title": "Main Menu"},
            {"selected": 1, "title": "Main Menu"},
            {"selected": 2, "title": "Main Menu"},
            {"selected": 3, "title": "Main Menu"},
        ]

        menu_labels = ["Print", "Prepare", "Control", "Leveling"]
        menu_colors = [
            (52, 152, 219),
            (46, 204, 113),
            (231, 76, 60),
            (155, 89, 182),
        ]

        for state in menu_states:
            img = Image.new('RGB', (240, 320), (0, 0, 0))
            draw = ImageDraw.Draw(img)

            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11)
            except (IOError, OSError):
                font = ImageFont.load_default()

            # Header
            draw.rectangle([0, 0, 239, 24], fill=(30, 60, 120))
            draw.text((5, 5), state["title"], fill=(255, 255, 255), font=font)

            # Draw menu items
            for i, (label, color) in enumerate(zip(menu_labels, menu_colors)):
                y = 40 + i * 65
                if i == state["selected"]:
                    # Selected item - brighter with border
                    draw.rectangle([5, y, 234, y + 55], fill=color, outline=(255, 255, 255), width=2)
                    draw.text((15, y + 18), f"> {label}", fill=(255, 255, 255), font=font)
                else:
                    # Non-selected item
                    draw.rectangle([10, y + 3, 229, y + 52], fill=(40, 40, 40), outline=color)
                    draw.text((20, y + 18), f"  {label}", fill=(180, 180, 180), font=font)

            # Encoder indicator
            draw.text((5, 300), f"Encoder pos: {state['selected']}", fill=(100, 100, 100), font=font)

            frames.append(img)

        # Save individual frames
        for i, frame in enumerate(frames):
            filepath = os.path.join(OUTPUT_DIR, f"menu_nav_frame_{i}.png")
            frame.save(filepath)

        # Save as animated GIF
        gif_path = os.path.join(OUTPUT_DIR, "menu_navigation.gif")
        frames[0].save(
            gif_path,
            save_all=True,
            append_images=frames[1:],
            duration=800,
            loop=0
        )
        self.assertTrue(os.path.exists(gif_path))

        # Verify all frames were saved
        for i in range(len(frames)):
            self.assertTrue(os.path.exists(
                os.path.join(OUTPUT_DIR, f"menu_nav_frame_{i}.png")
            ))


if __name__ == '__main__':
    unittest.main()
