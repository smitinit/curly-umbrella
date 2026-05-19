from reportlab.pdfbase import pdfmetrics, ttfonts
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
import os

PAGE_WIDTH, PAGE_HEIGHT = A4
FULL_COLUMN_WIDTH = PAGE_WIDTH - 1 * inch

# Font paths relative to this file's location (src/constants/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FONTS_DIR = os.path.join(BASE_DIR, "res", "fonts")

GARAMOND_REGULAR    = "Garamond_Regular"
GARAMOND_BOLD       = "Garamond_Bold"
GARAMOND_SEMIBOLD   = "Garamond_Semibold"
GARAMOND_ITALIC     = "Garamond_Italic"
GARAMOND_BOLD_ITALIC = "Garamond_BoldItalic"

pdfmetrics.registerFont(ttfonts.TTFont(GARAMOND_REGULAR,     os.path.join(FONTS_DIR, "EBGaramond-Regular.ttf")))
pdfmetrics.registerFont(ttfonts.TTFont(GARAMOND_BOLD,        os.path.join(FONTS_DIR, "EBGaramond-Bold.ttf")))
pdfmetrics.registerFont(ttfonts.TTFont(GARAMOND_SEMIBOLD,    os.path.join(FONTS_DIR, "EBGaramond-SemiBold.ttf")))
pdfmetrics.registerFont(ttfonts.TTFont(GARAMOND_ITALIC,      os.path.join(FONTS_DIR, "EBGaramond-Italic.ttf")))
pdfmetrics.registerFont(ttfonts.TTFont(GARAMOND_BOLD_ITALIC, os.path.join(FONTS_DIR, "EBGaramond-BoldItalic.ttf")))
