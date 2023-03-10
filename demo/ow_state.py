import ow_cv_class
import cv2 as cv
import time


class Player:
	def __init__(self, final_resolution, isMercy=False):
		self.owcv = ow_cv_class.ComputerVision(final_resolution=final_resolution)
		self.isMercy = isMercy
		self.in_killcam = False
		self.death_spectating = False
		self.heal_beam = False
		self.damage_beam = False
		self.saved_notifs = 0
		self.elim_notifs = 0
		self.assist_notifs = 0
		self.resurrecting = False
		self.being_beamed = False
		self.heal_beam_active_confs = 0
		self.damage_beam_active_confs = 0
		self.pos_required_confs = 1
		self.neg_required_confs = 8

	def refresh(self, frame_capture_only=False):
		self.owcv.capture_frame()
		if frame_capture_only:
			self.in_killcam = True
		else:
			self.in_killcam = self.owcv.detect_single("killcam")
		if not self.in_killcam:
			self.death_spectating = self.owcv.detect_single("death_spec")
			if not self.death_spectating:
				self.elim_notifs = self.owcv.detect_multiple("elimination")
				self.assist_notifs = self.owcv.detect_multiple("assist")
				self.saved_notifs = self.owcv.detect_multiple("saved")
				self.being_beamed = self.owcv.detect_single("being_beamed")
				if self.isMercy:
					self.detect_mercy_beams()
					if self.saved_notifs > 0:
						self.resurrecting = self.owcv.detect_single("resurrect_cd")

	def detect_mercy_beams(self):
		if self.owcv.detect_single("heal_beam"):
			if self.heal_beam_active_confs == self.pos_required_confs:
				if not self.heal_beam:
					self.heal_beam = True
					self.damage_beam = False
			else:
				if self.heal_beam_active_confs <= 0:
					self.heal_beam_active_confs = 1
				else:
					self.heal_beam_active_confs += 1
		else:
			if self.heal_beam_active_confs == (0 - self.neg_required_confs):
				if self.heal_beam:
					self.heal_beam = False
			else:
				if self.heal_beam_active_confs >= 0:
					self.heal_beam_active_confs = -1
				else:
					self.heal_beam_active_confs -= 1

		if self.owcv.detect_single("damage_beam"):
			if self.damage_beam_active_confs == self.pos_required_confs:
				if not self.damage_beam:
					self.damage_beam = True
					self.heal_beam = False
			else:
				if self.damage_beam_active_confs <= 0:
					self.damage_beam_active_confs = 1
				else:
					self.damage_beam_active_confs += 1
		else:
			if self.damage_beam_active_confs == (0 - self.neg_required_confs):
				if self.damage_beam:
					self.damage_beam = False
			else:
				if self.damage_beam_active_confs >= 0:
					self.damage_beam_active_confs = -1
				else:
					self.damage_beam_active_confs -= 1

	def start_tracking(self, refresh_rate):
		self.owcv.start_capturing(refresh_rate)

	def stop_tracking(self):
		self.owcv.stop_capturing()

	def benchmark(self, rounds=10):
		start_time = time.time()
		for i in range(0, rounds):
			self.refresh()
		duration = time.time() - start_time
		print(f"{duration} ({rounds}x)")

	def per_sec(self, seconds=2):
		counter = 0
		start_time = time.time()
		while time.time() < start_time + seconds:
			self.refresh(frame_capture_only=True)
			counter += 1
		print(f"Per second: {counter/seconds}")
		print(f"Average time: {round(1000 * (seconds/counter), 4)}ms")

#player = Player({"width":1920, "height":1080}, isMercy=True)
#player.per_sec(10)
