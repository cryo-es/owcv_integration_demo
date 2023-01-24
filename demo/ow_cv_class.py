import numpy as np
import cv2 as cv
from mss.windows import MSS as mss
import os


# "Also, it is a good thing to save the MSS instance inside an attribute of your class and calling it when needed."

def resource_path(relative_path):
	try:
		base_path = sys._MEIPASS
	except Exception:
		base_path = os.path.abspath(".")
	return os.path.join(base_path, relative_path)


class ComputerVision:
	def __init__(self, final_resolution={"height":1080,"width":1920}):
		self.resolution = {"height":1080, "width":1920}
		self.coords = {
			"elimination":[745, 853, 672, 960],
			"assist":[745, 853, 672, 960],
			"saved":[745, 853, 672, 960],
			"killcam":[89, 107, 41, 69],
			"death_spec":[66, 86, 1416, 1574],
			"heal_beam":[650, 730, 785, 860],
			"damage_beam":[650, 730, 1060, 1130],
			"resurrect_cd":[920, 1000, 1580, 1655]}
		self.scale_to_res(final_resolution)
		self.templates = {}
		for i in self.coords:
			self.templates[i] = cv.cvtColor(cv.imread(resource_path(f"t_{i}.png")), cv.COLOR_RGB2BGR)
		self.mask_names = ["heal_beam", "damage_beam"]
		self.masks = {}
		for i in self.mask_names:
			self.masks[i] = cv.imread(resource_path(f"m_{i}.png"))
		self.screen = mss()
		self.frame = []

	def scale_to_res(self, final_resolution):
		multiplier = {
		"height" : final_resolution["height"] / self.resolution["height"],
		"width" : final_resolution["width"] / self.resolution["width"]}

		if (multiplier["height"] != 1):
			for i in self.coords:
				self.coords[i][0] = int(self.coords[i][0] * multiplier["height"])
				self.coords[i][1] = int(self.coords[i][1] * multiplier["height"])
		if (multiplier["width"] != 1):
			for i in self.coords:
				self.coords[i][2] = int(self.coords[i][2] * multiplier["width"])
				self.coords[i][3] = int(self.coords[i][3] * multiplier["width"])
		self.resolution = final_resolution

	def capture_frame(self):
		#Probably can apply the colour transformation after matchTemplate
		self.frame = cv.cvtColor(np.array(self.screen.grab({"top":0, "left":0, "width":self.resolution["width"], "height":self.resolution["height"]})), cv.COLOR_RGB2BGR)

	def crop(self, image, template_name):
		return image[self.coords[template_name][0]:self.coords[template_name][1], self.coords[template_name][2]:self.coords[template_name][3]]

	def detect_multiple(self, template_name):
		if template_name in self.mask_names:
			result = cv.matchTemplate(self.crop(self.frame, template_name), self.templates[template_name], cv.TM_CCOEFF_NORMED, mask=self.masks[template_name])
		else:
			result = cv.matchTemplate(self.crop(self.frame, template_name), self.templates[template_name], cv.TM_CCOEFF_NORMED)
		cv.threshold(result, .9, 255, cv.THRESH_BINARY, result)
		return len(cv.findContours(result.astype(np.uint8), cv.RETR_LIST, cv.CHAIN_APPROX_SIMPLE)[0])

	def detect_single(self, template_name):
		if template_name in self.mask_names:
			result = cv.matchTemplate(self.crop(self.frame, template_name), self.templates[template_name], cv.TM_CCOEFF_NORMED, mask=self.masks[template_name])
		else:
			result = cv.matchTemplate(self.crop(self.frame, template_name), self.templates[template_name], cv.TM_CCOEFF_NORMED)
		return result.max() > .9