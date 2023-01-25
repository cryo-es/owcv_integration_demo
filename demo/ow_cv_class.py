import numpy as np
import cv2 as cv
from mss.windows import MSS as mss
import os


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
			"elimination":[749, 850, 831, 976],
			"assist":[749, 850, 831, 976],
			"saved":[749, 850, 727, 922],
			"killcam":[89, 107, 41, 69],
			"death_spec":[66, 86, 1416, 1574],
			"heal_beam":[658, 719, 793, 854],
			"damage_beam":[658, 719, 1065, 1126],
			"resurrect_cd":[920, 1000, 1580, 1655]}
		extremes = self.get_extremes()
		self.screenshot_region = {"top":extremes[0], "left":extremes[2], "height":extremes[1]-extremes[0], "width":extremes[3]-extremes[2]}
		self.scale_to_res(final_resolution, extremes)
		self.templates = {}
		for i in self.coords:
			#self.templates[i] = cv.cvtColor(cv.imread(resource_path(f"t_{i}.png")), cv.COLOR_RGB2BGR)
			self.templates[i] = cv.cvtColor(cv.imread(resource_path(f"t_{i}.png")), cv.COLOR_RGB2GRAY)
		self.mask_names = ["heal_beam", "damage_beam"]
		self.masks = {}
		for i in self.mask_names:
			#Wasn't doing RGB-BGR conversion on masks before, still seemed to work
			#self.masks[i] = cv.cvtColor(cv.imread(resource_path(f"m_{i}.png")), cv.COLOR_RGB2BGR)
			self.masks[i] = cv.cvtColor(cv.imread(resource_path(f"m_{i}.png")), cv.COLOR_RGB2GRAY)
		self.screen = mss()
		self.frame = []

	def get_extremes(self):
		extremes = [99999, 0, 99999, 0]
		for i in self.coords.values():
			if i[0] < extremes[0]:
				extremes[0] = i[0]
			if i[1] > extremes[1]:
				extremes[1] = i[1]
			if i[2] < extremes[2]:
				extremes[2] = i[2]
			if i[3] > extremes[3]:
				extremes[3] = i[3]
		return extremes

	def scale_to_res(self, final_resolution, extremes):
		multiplier = {
		"height" : final_resolution["height"] / self.resolution["height"],
		"width" : final_resolution["width"] / self.resolution["width"]}
		for i in self.coords:
			self.coords[i][0] = int(self.coords[i][0]-extremes[0] * multiplier["height"])
			self.coords[i][1] = int(self.coords[i][1]-extremes[0] * multiplier["height"])
			self.coords[i][2] = int(self.coords[i][2]-extremes[2] * multiplier["width"])
			self.coords[i][3] = int(self.coords[i][3]-extremes[2] * multiplier["width"])
		self.resolution = final_resolution

	def capture_frame(self):
		#self.frame = cv.cvtColor(np.array(self.screen.grab(self.screenshot_region)), cv.COLOR_RGB2BGR)
		self.frame = cv.cvtColor(np.array(self.screen.grab(self.screenshot_region)), cv.COLOR_RGB2GRAY)

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

#a = ComputerVision()
#a.frame = cv.cvtColor(cv.imread(resource_path("resurrected.png"))[66:1000, 41:1655], cv.COLOR_RGB2GRAY)
#cv.imshow("image", a.crop(a.frame, "resurrect_cd"))
#cv.waitKey(0)
#a.detect_single("resurrect_cd")
