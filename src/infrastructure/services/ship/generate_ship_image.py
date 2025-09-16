import io
import math
import random
from typing import Tuple

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


class ShipImageGenerator:
    """
    Generates a "ship" image for two users with avatars, names, percentage, progress bar, and a heart emoji.
    The final image is returned as PNG bytes.
    """

    CANVAS_WIDTH = 900
    CANVAS_HEIGHT = 420
    AVATAR_SIZE = 220
    PADDING = 36
    PROGRESS_BAR_HEIGHT = 34
    PROGRESS_BAR_RADIUS = 16
    EMOJI_SIZE = 236
    EMOJI_URLS = {
        "crying": "https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/72x72/1f62d.png", # 😭
        "neutral": "https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/72x72/1f610.png",# 😐
        "happy": "https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/72x72/1f60a.png",  # 😊
        "love": "https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/72x72/1f60d.png",   # 😍
        "heart": "https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/72x72/2764.png",   # ❤️
    }
    FONT_NAME_SIZE = 30
    FONT_PERCENTAGE_SIZE = 26
    FONT_TITLE_SIZE = 26
    RING_THICKNESS = 4
    BACKGROUND_GRADIENT_DEFAULT = ((30, 60, 140), (200, 120, 180))
    BACKGROUND_GRADIENT_HIGH = ((35, 150, 120), (80, 200, 150))
    BACKGROUND_GRADIENT_LOW = ((140, 50, 80), (200, 130, 110))
    MIN_HIGH_GRADIENT = 70
    MIN_LOW_GRADIENT = 35

    def __init__(self, first_user_name: str, second_user_name: str, percentage: float, image_url_first_user: str, image_url_second_user: str):
        """
        Initialize the ShipImageGenerator.
        """
        self.first_user_name = first_user_name
        self.second_user_name = second_user_name
        self.image_url_first_user = image_url_first_user
        self.image_url_second_user = image_url_second_user
        self.percentage = max(0.0, min(100.0, float(percentage)))

    def _get_image(self, url: str) -> Image.Image:
        """
        Download an image from a URL and return it as a PIL RGBA image.
        """
        resp = requests.get(url, stream=True)
        resp.raise_for_status()
        return Image.open(io.BytesIO(resp.content)).convert("RGBA")

    def _generate_random_gradient_background(
        self, color_start: Tuple[int, int, int], color_end: Tuple[int, int, int]
    ) -> Image.Image:
        """
        Generate a background with gradient, subtle noise, and vignette effect.
        """
        w, h = self.CANVAS_WIDTH, self.CANVAS_HEIGHT

        base = Image.new("RGB", (w, h), color_start)
        top = Image.new("RGB", (w, h), color_end)
        mask = Image.new("L", (w, h))
        # create vertical gradient mask with tiny random jitter
        mask.putdata([int((y / (h - 1) + (random.random() - 0.5) * 0.02) * 255) for y in range(h) for _ in range(w)])
        gradient = Image.composite(top, base, mask)

        noise = Image.effect_noise((w, h), 64).convert("L").filter(ImageFilter.GaussianBlur(radius=10))
        color_layer1 = Image.new("RGB", (w, h), tuple(int(c * 0.7) for c in color_start))
        color_layer2 = Image.new("RGB", (w, h), tuple(int(c * 0.9) for c in color_end))
        colored_noise = Image.composite(color_layer2, color_layer1, noise)
        final = Image.blend(gradient, colored_noise, alpha=0.25)

        vignette = Image.new("L", (w, h), 0)
        draw_v = ImageDraw.Draw(vignette)
        max_radius = math.hypot(w / 2, h / 2)
        for i in range(0, int(max_radius), 6):
            val = int(255 * (i / max_radius))
            draw_v.ellipse([(w / 2 - i, h / 2 - i), (w / 2 + i, h / 2 + i)], fill=val)
        vignette = vignette.filter(ImageFilter.GaussianBlur(radius=80))
        final = Image.composite(final, Image.new("RGB", final.size, (0, 0, 0)), vignette)

        return final

    def _convert_to_circular(self, image: Image.Image, size: int) -> Image.Image:
        """
        Convert an image to a circular avatar.
        """
        img = ImageOps.fit(image, (size, size), centering=(0.5, 0.5))
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
        img.putalpha(mask)
        return img

    def _draw_progress_bar(
        self,
        draw: ImageDraw.ImageDraw,
        top_left: Tuple[int, int],
        bar_size: Tuple[int, int],
        percentage: float,
        radius: int,
    ):
        """
        Draw a rounded progress bar with given percentage.
        """
        x, y = top_left
        w, h = bar_size
        # background of bar (semi translucent)
        draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=(255, 255, 255, 90))
        fill_w = int((percentage / 100.0) * w)
        if fill_w > 6:
            # inner filled area inset a bit for padding/rounded corners
            draw.rounded_rectangle([x + 3, y + 3, x + fill_w - 3, y + h - 3],
                                   radius=max(1, radius - 4),
                                   fill=(255, 80, 100))
        elif fill_w > 0:
            # very small fill: draw a narrow rounded rect safely
            draw.rectangle([x + 3, y + 3, x + max(4, fill_w), y + h - 3], fill=(255, 80, 100))
        # outline
        draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, outline=(255, 255, 255, 160), width=2)

    def _draw_emoji(self, base: Image.Image, center: Tuple[int, int], size: int):
        """
        Selects an emoji URL based on the percentage, downloads it, and draws it.
        """
        if self.percentage <= 20:
            emoji_key = "crying"
        elif self.percentage <= 40:
            emoji_key = "neutral"
        elif self.percentage <= 70:
            emoji_key = "happy"
        elif self.percentage <= 90:
            emoji_key = "love"
        else:  # 91-100%
            emoji_key = "heart"

        emoji_url = self.EMOJI_URLS[emoji_key]

        try:
            emoji_img = self._get_image(emoji_url)

            emoji_img = emoji_img.resize((size, size), Image.Resampling.LANCZOS)

            cx, cy = center
            paste_x = cx - size // 2
            paste_y = cy - size // 2

            base.paste(emoji_img, (paste_x, paste_y), emoji_img)

        except requests.exceptions.RequestException as e:
            pass

    def _draw_user_names(self, canvas: Image.Image):
        """
        Draw the first and second user names below their avatars.
        """
        draw = ImageDraw.Draw(canvas)
        try:
            font_names = ImageFont.truetype("DejaVuSans.ttf", self.FONT_NAME_SIZE)
        except Exception:
            font_names = ImageFont.load_default()

        width = self.CANVAS_WIDTH
        avatars_y = int((self.CANVAS_HEIGHT - self.AVATAR_SIZE) * 0.22)
        name_y = avatars_y + self.AVATAR_SIZE + 12
        left_x = self.PADDING
        right_x = width - self.PADDING - self.AVATAR_SIZE

        w1 = font_names.getlength(self.first_user_name)
        draw.text((left_x + self.AVATAR_SIZE / 2 - w1 / 2, name_y),
                self.first_user_name, font=font_names, fill=(255, 255, 255, 230))

        w2 = font_names.getlength(self.second_user_name)
        draw.text((right_x + self.AVATAR_SIZE / 2 - w2 / 2, name_y),
                self.second_user_name, font=font_names, fill=(255, 255, 255, 230))

    def _draw_percentage_text(self, canvas: Image.Image):
        """
        Draw the percentage text above the progress bar.
        """
        draw = ImageDraw.Draw(canvas)
        try:
            font_percentage = ImageFont.truetype("DejaVuSans-Bold.ttf", self.FONT_PERCENTAGE_SIZE)
        except Exception:
            font_percentage = ImageFont.load_default()

        width = self.CANVAS_WIDTH
        # calcula posição do progress bar
        avatars_y = int((self.CANVAS_HEIGHT - self.AVATAR_SIZE) * 0.22)
        name_y = avatars_y + self.AVATAR_SIZE + 12
        try:
            font_names = ImageFont.truetype("DejaVuSans.ttf", self.FONT_NAME_SIZE)
        except Exception:
            font_names = ImageFont.load_default()
        bbox_name = font_names.getbbox(self.first_user_name)
        h1 = bbox_name[3] - bbox_name[1] # height = bottom - top

        bar_y = int(name_y + h1 + 28)
        perc_text = f"{int(round(self.percentage))}%"

        bbox_perc = font_percentage.getbbox(perc_text)
        tw = bbox_perc[2] - bbox_perc[0] # width = right - left
        th = bbox_perc[3] - bbox_perc[1] # height = bottom - top

        draw.text((width / 2 - tw / 2, bar_y - th - 6), perc_text, font=font_percentage, fill=(255, 255, 255, 255))

    def _create_canvas_with_background(self, background: Image.Image) -> Image.Image:
        """
        Create the main canvas and paste the background onto it.
        """
        width, height = self.CANVAS_WIDTH, self.CANVAS_HEIGHT
        canvas = Image.new("RGBA", (width, height))
        canvas.paste(background, (0, 0))
        return canvas

    def _paste_avatars_with_rings(self, canvas: Image.Image, a1: Image.Image, a2: Image.Image):
        """
        Paste circular avatars with rings onto the canvas.
        """
        width, height = self.CANVAS_WIDTH, self.CANVAS_HEIGHT
        avatars_y = int((height - self.AVATAR_SIZE) * 0.22)
        left_x = self.PADDING
        right_x = width - self.PADDING - self.AVATAR_SIZE

        ring_size = self.AVATAR_SIZE + 2 * self.RING_THICKNESS
        ring = Image.new("RGBA", (ring_size, ring_size), (255, 255, 255, 0))
        ImageDraw.Draw(ring).ellipse((0, 0, ring_size, ring_size), fill=(255, 255, 255, 200))
        ring_mask = ring.split()[-1]

        # avatars com anéis
        canvas.paste(ring, (left_x - self.RING_THICKNESS, avatars_y - self.RING_THICKNESS), ring_mask)
        canvas.paste(a1, (left_x, avatars_y), a1)

        canvas.paste(ring, (right_x - self.RING_THICKNESS, avatars_y - self.RING_THICKNESS), ring_mask)
        canvas.paste(a2, (right_x, avatars_y), a2)

    def _get_draw_context(self, canvas: Image.Image) -> ImageDraw.ImageDraw:
        """Return a drawing context for the canvas."""
        return ImageDraw.Draw(canvas)

    def _calculate_bar_size(self, canvas: Image.Image) -> Tuple[int, int]:
        """
        Calculate the size (width, height) of the progress bar based on positions of avatars.
        """
        width = self.CANVAS_WIDTH
        # space between avatars
        left_x = self.PADDING
        right_x = width - self.PADDING - self.AVATAR_SIZE
        space_between = right_x - (left_x + self.AVATAR_SIZE)
        bar_w = max(180, int(space_between - 40))
        bar_h = self.PROGRESS_BAR_HEIGHT
        return (bar_w, bar_h)

    def _calculate_bar_position(self, canvas: Image.Image) -> Tuple[int, int]:
        """
        Calculate the top-left position for the progress bar so it's centered between avatars.
        """
        width = self.CANVAS_WIDTH
        avatars_y = int((self.CANVAS_HEIGHT - self.AVATAR_SIZE) * 0.22)
        name_y = avatars_y + self.AVATAR_SIZE + 12

        try:
            font_names = ImageFont.truetype("DejaVuSans.ttf", self.FONT_NAME_SIZE)
        except Exception:
            font_names = ImageFont.load_default()
        # measure name height to place the bar below names
        bbox_name = font_names.getbbox(self.first_user_name)
        h1 = bbox_name[3] - bbox_name[1]

        bar_y = int(name_y + h1 + 28)

        bar_y = int(name_y + h1 + 28)

        # center horizontally between avatars
        left_x = self.PADDING
        right_x = width - self.PADDING - self.AVATAR_SIZE
        space_between = right_x - (left_x + self.AVATAR_SIZE)
        bar_w, bar_h = self._calculate_bar_size(canvas)
        bar_x = left_x + self.AVATAR_SIZE + (space_between - bar_w) // 2

        return (int(bar_x), int(bar_y))

    def _calculate_heart_position(self) -> Tuple[int, int]:
        """
        Calculate a good place for the heart: centered between avatars, slightly above their vertical center.
        """
        width = self.CANVAS_WIDTH
        height = self.CANVAS_HEIGHT
        avatars_y = int((height - self.AVATAR_SIZE) * 0.22)
        center_x = width // 2
        center_y = avatars_y + (self.AVATAR_SIZE // 2) - 10
        return (int(center_x), int(center_y))


    def _compose_image(self) -> Image.Image:
        """
        Compose the final ship image.
        """
        if self.percentage > self.MIN_HIGH_GRADIENT:
            start, end = self.BACKGROUND_GRADIENT_HIGH
        elif self.percentage < self.MIN_LOW_GRADIENT:
            start, end = self.BACKGROUND_GRADIENT_LOW
        else:
            start, end = self.BACKGROUND_GRADIENT_DEFAULT

        background = self._generate_random_gradient_background(start, end)

        a1 = self._convert_to_circular(self._get_image(self.image_url_first_user), self.AVATAR_SIZE)
        a2 = self._convert_to_circular(self._get_image(self.image_url_second_user), self.AVATAR_SIZE)

        canvas = self._create_canvas_with_background(background)

        self._paste_avatars_with_rings(canvas, a1, a2)

        # heart
        self._draw_emoji(canvas, self._calculate_heart_position(), self.EMOJI_SIZE)

        # progress bar
        draw_ctx = self._get_draw_context(canvas)
        bar_pos = self._calculate_bar_position(canvas)
        bar_size = self._calculate_bar_size(canvas)
        self._draw_progress_bar(draw_ctx, bar_pos, bar_size, self.percentage, self.PROGRESS_BAR_RADIUS)

        self._draw_user_names(canvas)
        self._draw_percentage_text(canvas)

        return canvas

    def get_image(self) -> bytes:
        """
        Generate the final ship image and return it as PNG bytes.
        """
        final_img = self._compose_image()
        bytes_obj = io.BytesIO()
        final_img.save(bytes_obj, format="PNG")
        bytes_obj.seek(0)
        return bytes_obj.getvalue()