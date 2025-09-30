"""
Python Andy Warhol Style Image Editor
Engineer Your World
By Benjamin Garcia
Last Updated 9/19/2025

CustomTkinter Documentation https://customtkinter.tomschimansky.com/documentation/
"""

import cv2
import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageTk
import eyw
import numpy as np
from io import BytesIO
import colorsys
import math

# Make window look cool
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# converts a hex value to a rgb tuple
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')  # Remove '#' if present
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

# converts an rgb tuple to a hex value
def rgb_to_hex(rgb_color):
    r, g, b = rgb_color
    return f'#{int(r):02x}{int(g):02x}{int(b):02x}'

# return a smaller easier to work with image
def compress_image(image, screen_size, quality=100):
    pil_image = Image.fromarray(image)

    screen_width, screen_height = screen_size

    screen_width = screen_width * 0.6
    screen_height = screen_height * 0.6

    width, height = pil_image.size

    if width >= screen_width and height >= screen_height:
        width_scale = width/screen_width
        height_scale = height/screen_height

        if width_scale > height_scale:
            width = width // width_scale
            height = height // width_scale
        else:
            width = width // height_scale
            height = height // height_scale

    pil_image = pil_image.resize((int(width), int(height)))

    # Saves the new smaller image to memory instead of disk
    buffer = BytesIO()
    pil_image.save(buffer, format="JPEG", quality=quality, optimize=True)
    buffer.seek(0)

    # converts image to numpy array because that's what opencv uses
    return np.array(Image.open(buffer))

# Opens image and converts it to RGB gray_scale
def open_gray_scale(file, screen_size):
    image_gs_simple = cv2.imread(file, 0)

    image_gs_simple_compressed = compress_image(image_gs_simple, screen_size)

    return cv2.cvtColor(image_gs_simple_compressed, cv2.COLOR_GRAY2RGB), cv2.cvtColor(image_gs_simple, cv2.COLOR_GRAY2RGB)

# Opens image and converts it to RGB
def open_to_rgb(file, screen_size):
    image_og = cv2.imread(file, 1)

    image_og_compressed = compress_image(image_og, screen_size)

    return cv2.cvtColor(image_og_compressed, cv2.COLOR_BGR2RGB)

# Creates papers, masks, and applies and combines them
def customize(image, breaks, colors):

    # Creating colored paper
    papers = []
    for color in colors:
        papers.append(
            eyw.create_colored_paper(image, color[0], color[1], color[2])
        )

    # Creating masks
    masks = []

    for i in range(len(colors)):
        if i == 0:
            masks.append(
                eyw.create_mask(
                    image,
                    [0, 0, 0],
                    [breaks[i], breaks[i], breaks[i]]
                )
            )
        elif colors[i] == colors[-1]:
            masks.append(
                eyw.create_mask(
                    image,
                    [breaks[i - 1] + 1, breaks[i - 1] + 1, breaks[i - 1] + 1],
                    [255, 255, 255]
                )
            )
        else:
            masks.append(
                eyw.create_mask(
                    image,
                    [breaks[i-1] + 1, breaks[i-1] + 1, breaks[i-1] + 1],
                    [breaks[i], breaks[i], breaks[i]]
                )
            )

    # Combining applying masks
    parts = []
    for i in range(len(colors)):
        parts.append(
            eyw.apply_mask(papers[i], masks[i])
        )

    # Combing masks and colored paper
    customized_image = eyw.combine_images(parts[0], parts[1])
    for i in range(len(parts)):
        if i >= 2:
            customized_image = eyw.combine_images(customized_image, parts[i])

    return customized_image

# Turns image into a CTKImage
def create_ctk_image(image):
    pil_image = Image.fromarray(image)

    return ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=pil_image.size)

class SimpleColorPicker(ctk.CTkToplevel):
    def __init__(self, master=None, callback=None, size=300, color=(49, 107, 65)):
        super().__init__(master)
        self.title = "SimpleColorPicker"
        self.geometry("300x250")
        self.callback = callback

        self.color = color
        self.hex_text = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"

        r, g, b = color

        self.hue, self.sat, self.val = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)

        self.size = size
        self.radius = size // 2
        self.marker_id = None

        wheel = self._create_color_wheel()
        self.tk_img = ImageTk.PhotoImage(wheel)

        # Canvas to display wheel
        self.canvas = ctk.CTkCanvas(self, width=size, height=size, bg="white", highlightthickness=0)
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
        self.canvas.grid(row=0, column=0, padx=20, pady=20)

        self.slider = ctk.CTkSlider(self, width=size, command=self._update_value)
        self.slider.grid(row=1, column=0, padx=10)

        self.slider.set(self.val)

        # Container frame
        self.preview = ctk.CTkFrame(self, width=size, height=100, fg_color=self.hex_text)
        self.preview.grid(row=2, column=0, padx=10, pady=20)

        # Label inside frame
        self.text = ctk.CTkEntry(self.preview, width=70, height=30, text_color="#ffffff", fg_color="#000000")
        self.text.pack(padx=75, pady=5)

        apply_button = ctk.CTkButton(self, width=size, height=40, text="Apply", command=self.apply)
        apply_button.grid(row=3, column=0, padx=10, pady=20)

        self.text.insert(-1, self.hex_text)

        # Bind mouse click
        self.canvas.bind("<Button-1>", self.pick_color)
        self.canvas.bind("<B1-Motion>", self.pick_color)
        self.canvas.bind("<ButtonRelease-1>", self.pick_color)
        self.text.bind("<Key>", self.hex_input)

        theta = (self.hue * 2 * math.pi)  # radians
        radius = self.sat

        cx = cy = self.size // 2  # Center of the color wheel
        r_pixels = radius * (self.size // 2)  # scale to pixels

        # polar coords to cartesian coords
        x = cx + r_pixels * -math.cos(theta)
        y = cy + r_pixels * -math.sin(theta)

        self.place_marker(x, y)  # moving the marker into place

    def pick_color(self, event):
        dx = event.x - self.radius
        dy = event.y - self.radius
        r = np.sqrt(dx*dx + dy*dy) / self.radius

        if r <= 1:  # inside the wheel
            theta = np.arctan2(dy, dx)
            self.hue = (theta + np.pi) / (2*np.pi)
            self.sat = r
            rgb = colorsys.hsv_to_rgb(self.hue, self.sat, self.val)
            rgb = tuple(int(c*255) for c in rgb)
            hex_val = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

            # update preview
            self.preview.configure(fg_color=hex_val)

            for i in range(len(self.hex_text)):
                self.text.delete(0, len(self.hex_text))

            self.text.insert(-1, hex_val)

            self.hex_text = self.text.get()

            # place/update marker
            self.place_marker(event.x, event.y)

    def hex_input(self, event):
        if event.keycode == 8:
            self.hex_text = self.text.get()[:-1]
        else:
            self.hex_text = self.text.get() + event.char

        length = len(self.hex_text)

        try:
            if self.hex_text[0] != "#" and len(self.hex_text) > 0:
                self.text.insert(0, "#")
                self.hex_text = self.text.get()
        except IndexError:
            self.text.insert(-1, "#")

        if length == 7:
            try:
                r = int(self.hex_text[1:3], 16) / 255
                g = int(self.hex_text[3:5], 16) / 255
                b = int(self.hex_text[5:7], 16) / 255

                self.hue, self.sat, self.val = colorsys.rgb_to_hsv(r, g, b)

                self.preview.configure(fg_color=self.hex_text)

                self.slider.set(self.sat)

                theta = (self.hue * 2 * math.pi)  # radians
                radius = self.sat

                cx = cy = self.size // 2 # Center of the color wheel
                r_pixels = radius * (self.size // 2) # scale to pixels

                # polar coords to cartesian coords
                x = cx + r_pixels * -math.cos(theta)
                y = cy + r_pixels * -math.sin(theta)

                self.place_marker(x, y) # moving the marker into place
            except ValueError:
                pass

    def place_marker(self, x, y):
        r = 6  # radius of marker circle
        if self.marker_id is None:
            # first time: create a new oval
            self.marker_id = self.canvas.create_oval(
                x-r, y-r, x+r, y+r,
                outline="black", width=2, fill=""
            )
        else:
            # move existing oval
            self.canvas.coords(self.marker_id, x-r, y-r, x+r, y+r)

    def _update_value(self, value):
        self.val = value
        # update the preview
        rgb = colorsys.hsv_to_rgb(self.hue, self.sat, self.val)
        rgb = tuple(int(c * 255) for c in rgb)
        hex_val = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

        self.preview.configure(fg_color=hex_val)

        for i in range(len(self.hex_text)):
            self.text.delete(0, len(self.hex_text))

        self.text.insert(-1, hex_val)

        self.hex_text = self.text.get()

    def _create_color_wheel(self, size=300):
        radius = size // 2
        img = np.zeros((size, size, 3), dtype=np.uint8)

        for y in range(size):
            for x in range(size):
                dx = x - radius
                dy = y - radius
                r = np.sqrt(dx * dx + dy * dy) / radius
                if r <= 1:  # inside circle
                    theta = np.arctan2(dy, dx)
                    hue = (theta + np.pi) / (2 * np.pi)
                    sat = r
                    val = 1.0
                    rgb = colorsys.hsv_to_rgb(hue, sat, val)
                    img[y, x] = [int(c * 255) for c in rgb]
                if r > 1:
                    img[y, x] = [36,36,36] # The color of the background

        return Image.fromarray(img)

    def apply(self):
        try:
            text = self.text.get()[1:]

            r = int(text[0:2], 16)
            g = int(text[2:4], 16)
            b = int(text[4:6], 16)

            self.color = (r, g, b)
        except ValueError:
            pass

        if self.callback:
            self.callback(self.color, self.text.get())
        self.destroy()

class Color(ctk.CTkFrame):
    def __init__(self, master, color, painting, position):
        self.color = color
        self.painting = painting
        self.position = position

        super().__init__(
            master=master,
            fg_color="transparent"
        )
        self.pack(side="left", padx=0)

        self.color_button = ctk.CTkButton(
            master=self,
            width=28,
            text="",
            fg_color=rgb_to_hex(self.color),
            command=self._choose_color
        )
        self.color_button.pack(side="right", padx=2)

        if self.position > 0:
            self.gs_button = ctk.CTkButton(
                master=self,
                width=14,
                height=28,
                text="",
                command=self.choose_grayscale
            )
            self.gs_button.pack(side="right", padx=2)
            if self.position == 1:
                self.choose_grayscale()

    def _choose_color(self):
        def on_color_picked(rgb_color, hex_color):
            self.color = rgb_color
            self.color_button.configure(fg_color=hex_color)
            self.painting._update_colors()

        pick_color = SimpleColorPicker(color=self.color)
        pick_color.callback = on_color_picked

    def choose_grayscale(self):
        self.gs_button.configure(fg_color="#0C2940")
        self.painting.slider_gs.set(self.painting.breaks[self.position-1])
        self.painting.chosen_gs = self.position-1
        for button in self.painting.color_buttons:
            button.unselect(self.position)

    def unselect(self, selected):
        if self.position > 0 and self.position != selected:
            self.gs_button.configure(fg_color="#1F6AA5")

# Class that holds and configures the images
class Painting:
    def __init__(self, file_path, root, screen_size):
        self.breaks = [
            120
        ]
        self.colors = [
            (0,0,255),
            (255,0,0)
        ]

        self.chosen_gs = 0

        # Takes something like "C:\Users\User\Photos\cat.jpeg" and extracts "cat.jpeg"
        self.name = file_path.split('/')[-1]

        # Creating inital images
        self.image_rgb = open_to_rgb(file_path, screen_size)
        self.image_gs, self.og_gs = open_gray_scale(file_path, screen_size)
        self.image_cstm = customize(self.image_gs, self.breaks, self.colors)

        self.root = root

        self.images = [ # Images as CTKImages
            ["Customized", create_ctk_image(self.image_cstm)],
            ["Original", create_ctk_image(self.image_rgb)],
            ["Gray Scale", create_ctk_image(self.image_gs)],
        ]

        self.color_buttons = []
        self.image_buttons = []

        self.image_label = None # The label that is used for changing the displayed image

        self.current = None

        self.color_frame = None

        self.slider_gs = None

    def display(self):
        if self.name not in self.root._tab_dict: #Checks if this painting already has a tab created
            self.root.add(self.name)

            frame = self._create_frame(self.root)
            frame.grid(row=0, column=0, sticky="nsew")

            self._switch_image(self.images[0][0])

    def _create_frame(self, root):
        tab = root.tab(self.name)

        # Frame to hold the images
        image_frame = ctk.CTkFrame(tab, fg_color="transparent")
        image_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Allow image_frame’s single column to expand
        tab.grid_columnconfigure(0, weight=1)
        image_frame.grid_columnconfigure(0, weight=1)

        # Buttons row
        button_frame = ctk.CTkFrame(image_frame, fg_color="transparent")
        button_frame.grid(row=0, column=0, pady=10, sticky="n")

        # Frame to hold the color buttons
        self.color_frame = ctk.CTkFrame(image_frame, fg_color="transparent")
        self.color_frame.grid(row=1, column=0, pady=10, sticky="n")

        # Frame for grayscale slider
        slider_frame = ctk.CTkFrame(image_frame, fg_color="transparent")
        slider_frame.grid(row=2, column=0, pady=10, sticky="n")

        # Slider to change grayscale
        self.slider_gs = ctk.CTkSlider(master=slider_frame, from_=0, to=254, number_of_steps=254, command=self._update_gs)
        self.slider_gs.pack(side="left", padx=5)

        # Creating a button for each image
        for i in self.images:
            image_button = ctk.CTkButton(
                master=button_frame,
                text=i[0],
                command=lambda x=i: self._switch_image(x[0])
            )
            image_button.pack(side="left", padx=5)
            self.image_buttons.append([i[0], image_button])

        # Creating a button for each color
        for color in self.colors:
            self.color_buttons.append(
                Color(
                    master=self.color_frame,
                    color=color,
                    painting=self,
                    position=len(self.color_buttons)
                )
            )

        # Creating a bold font for buttons
        bold = ctk.CTkFont(family="Helvetica", size=18, weight="bold")

        # WIP Button for adding colors
        add_button = ctk.CTkButton(
            master=self.color_frame,
            width=28,
            text="+",
            text_color="#000000",
            font=bold,
            command=lambda: self._add_color()
        )
        add_button.pack(side="right", padx=5)

        # WIP Button for removing colors
        sub_button = ctk.CTkButton(
            master=self.color_frame,
            width=28,
            text="-",
            text_color="#000000",
            font=bold,
            command=lambda: self._sub_color()
        )
        sub_button.pack(side="right", padx=5)

        # Image row
        self.current = self.images[0][0]
        self.image_label = ctk.CTkLabel(master=image_frame, image=self.images[0][1], text="")
        self.image_label.grid(row=3, column=0, pady=10, sticky="n")

        return image_frame

    def _add_color(self):
        color = self.colors[-1]
        self.colors.append(color)
        self.color_buttons.append(
            Color(
                master=self.color_frame,
                color=color,
                painting=self,
                position=len(self.color_buttons)
            )
        )

        for i in range(len(self.breaks)):
            num = self.breaks[-(i+1)]
            if num != 254 - i:
                break
            else:
                self.breaks[-(i+1)] = self.breaks[-(i+1)] - 1

        self.breaks.append(254)

        self.color_buttons[-1].choose_grayscale()

        self._update_colors()

    def _sub_color(self):
        if len(self.colors) > 2:
            self.colors.pop()

            self.color_buttons[-1].destroy()
            self.color_buttons.pop()

            self.breaks.pop()

            self._update_colors()

    def _update_colors(self):
        for i in range(len(self.color_buttons)):
            self.colors[i] = self.color_buttons[i].color

        self._update_images()


    def _switch_image(self, image): #Changes displayed image
        for button in self.image_buttons:
            button[1].configure(fg_color="#1F6AA5")
            if button[0] == image:
                button[1].configure(fg_color="#0C2940")

        for label in self.images:
            if label[0] == image:
                self.image_label.configure(image=label[1])
                self.current = label[0]

    # Changes the image currently viewed (Customized, Original. Grayscale)
    def _update_current(self, image):
        self.image_label.configure(image=image)

    def _update_gs(self, value):
        max = 254
        min = 0

        if len(self.breaks) == 1:
            pass
        elif self.chosen_gs == 0:
            max = self.breaks[self.chosen_gs+1]
        elif self.breaks[self.chosen_gs] == self.breaks[-1]:
            min = self.breaks[self.chosen_gs-1]
        else:
            max = self.breaks[self.chosen_gs + 1]
            min = self.breaks[self.chosen_gs - 1]

        if value >= max:
            value = max - 1
        elif value <= min:
            value = min + 1
        self.slider_gs.set(value)
        self.breaks[self.chosen_gs] = value
        self._update_images()

    # Replaces images in self.images with new updated ones
    def _update_images(self):
        self.image_cstm = customize(self.image_gs, self.breaks, self.colors)
        self.images = [  # Images as CTKImages
            ["Customized", create_ctk_image(self.image_cstm)],
            ["Original", create_ctk_image(self.image_rgb)],
            ["Gray Scale", create_ctk_image(self.image_gs)],
        ]
        if self.current == self.images[0][0]:
            self._update_current(self.images[0][1])

    def get_image(self, name):
        if name == self.name:
            return customize(self.og_gs, self.breaks, self.colors)
        return None


# Class that controls the general app
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.screen_size = (self.winfo_screenwidth(), self.winfo_screenheight())

        # Creating holder for buttons and the buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(side="top", anchor="w", pady=10)

        open_button = ctk.CTkButton(master=button_frame, text="Open", command=self._open)
        open_button.pack(side="left", padx=5)

        save_button = ctk.CTkButton(master=button_frame, text="Save", command=self._save)
        save_button.pack(side="left", padx=5)

        # Creating tab viewer
        self.tab_view = ctk.CTkTabview(master=self)
        self.tab_view.pack(side="top", fill="both", expand=True, padx=20, pady=20)

        self.paintings = []

    # Prompts user to select an image
    def _open(self):
        file = filedialog.askopenfilename(
            title="Select a file",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg")]
        )

        # Creates a new Painting object with the selected file
        if file:
            self.paintings.append(Painting(file, self.tab_view, self.screen_size))
            self._display()
            self.tab_view.set(file.split('/')[-1])

    def _save(self):
        current = self.tab_view.get() # Getting current open image
        image = None
        for painting in self.paintings: # Asking each painting for their image
            response = painting.get_image(current)
            if isinstance(response, np.ndarray):
                image = Image.fromarray(response) # Converting numpy.ndarray into valid image format

        # Asking user where to save image and what to call it
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg")]
        )

        # Save the image
        image.save(filename)

    # Tells the painting classes to display
    def _display(self):
        for painting in self.paintings:
            painting.display()


# Define an App class and start the main loop
app = App()
app.focus()
app.title("AWIM") # Andy Warhol Image Maker
app.state("zoomed")
app.mainloop()