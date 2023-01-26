import numpy as np
import cv2 as cv
import dxcam
import os


def resource_path(relative_path):
	try:
		base_path = sys._MEIPASS
	except Exception:
		base_path = os.path.abspath(".")
	return os.path.join(base_path, relative_path)


class ComputerVision:
	def __init__(self, final_resolution={"width":1920, "height":1080}):
		self.base_resolution = {"width":1920, "height":1080}
		self.final_resolution = final_resolution
		self.coords = {
			"elimination":[749, 850, 832, 976],
			"assist":[749, 850, 832, 976],
			"saved":[749, 850, 727, 922],
			"killcam":[89, 107, 41, 69],
			"death_spec":[66, 86, 1416, 1574],
			"heal_beam":[658, 719, 793, 854],
			"damage_beam":[658, 719, 1065, 1126],
			"resurrect_cd":[920, 1000, 1580, 1655],
			"being_beamed":[762, 807, 460, 508]}
		self.screenshot_region = (0, 0, final_resolution["width"], final_resolution["height"])
		self.templates = {}
		for i in self.coords:
			self.templates[i] = cv.cvtColor(cv.imread(resource_path(f"t_{i}.png")), cv.COLOR_RGB2GRAY)
		self.mask_names = ["heal_beam", "damage_beam"]
		self.masks = {}
		for i in self.mask_names:
			self.masks[i] = cv.cvtColor(cv.imread(resource_path(f"m_{i}.png")), cv.COLOR_RGB2GRAY)
		self.screen = dxcam.create(output_color="GRAY")
		self.frame = []

	def start_capturing(self, capture_fps=60):
		self.screen.start(target_fps=capture_fps, video_mode=True)

	def stop_capturing(self):
		self.screen.stop()

	def capture_frame(self):
		if self.final_resolution != self.base_resolution:
			self.frame = cv.resize(self.screen.get_latest_frame(), (self.base_resolution["width"], self.base_resolution["height"]))
		else:
			self.frame = self.screen.get_latest_frame()

	def crop(self, image, template_name):
		return image[self.coords[template_name][0]:self.coords[template_name][1], self.coords[template_name][2]:self.coords[template_name][3]]

	def match(self, template_name):
		if template_name in self.mask_names:
			return cv.matchTemplate(self.crop(self.frame, template_name), self.templates[template_name], cv.TM_CCOEFF_NORMED, mask=self.masks[template_name])
		else:
			return cv.matchTemplate(self.crop(self.frame, template_name), self.templates[template_name], cv.TM_CCOEFF_NORMED)

	def detect_multiple(self, template_name):
		result = self.match(template_name)
		cv.threshold(result, .9, 255, cv.THRESH_BINARY, result)
		return len(cv.findContours(result.astype(np.uint8), cv.RETR_LIST, cv.CHAIN_APPROX_SIMPLE)[0])

	def detect_single(self, template_name):
		result = self.match(template_name)
		return result.max() > .9
