import ow_cv_class as owcv
import cv2 as cv
import time

class Player:
	def __init__(self, isMercy=False):
		self.ow = owcv.ComputerVision()
		self.isMercy = isMercy
		self.in_killcam = False
		self.death_spectating = False
		self.heal_beam = False
		self.damage_beam = False
		self.saved_notifs = 0
		self.elim_notifs = 0
		self.assist_notifs = 0
		self.resurrecting = False
		self.heal_beam_active_confs = 0
		self.damage_beam_active_confs = 0
		self.pos_required_confs = 1
		self.neg_required_confs = 8

	def refresh(self):
		self.ow.capture_frame()
		self.in_killcam = self.ow.detect_single("killcam")
		#self.in_killcam = True
		if not self.in_killcam:
			self.death_spectating = self.ow.detect_single("death_spec")
			#self.death_spectating = True
			if not self.death_spectating:
				self.elim_notifs = self.ow.detect_multiple("elimination")
				self.assist_notifs = self.ow.detect_multiple("assist")
				self.saved_notifs = self.ow.detect_multiple("saved")
				if self.isMercy:
					self.detect_mercy_beams()
					if self.saved_notifs > 0:
						self.resurrecting = self.ow.detect_single("resurrect_cd")

	def detect_mercy_beams(self):
		if self.ow.detect_single("heal_beam"):
			if self.heal_beam_active_confs == self.pos_required_confs:
				if not self.heal_beam:
					self.heal_beam = True
					self.damage_beam = False
			else:
				if self.heal_beam_active_confs < 0:
					self.heal_beam_active_confs = 1
				else:
					self.heal_beam_active_confs += 1
		else:
			if self.heal_beam_active_confs == (0 - self.neg_required_confs):
				if self.heal_beam:
					self.heal_beam = False
			else:
				if self.heal_beam_active_confs > 0:
					self.heal_beam_active_confs = -1
				else:
					self.heal_beam_active_confs -= 1

		if self.ow.detect_single("damage_beam"):
			if self.damage_beam_active_confs == self.pos_required_confs:
				if not self.damage_beam:
					self.damage_beam = True
					self.heal_beam = False
			else:
				if self.damage_beam_active_confs < 0:
					self.damage_beam_active_confs = 1
				else:
					self.damage_beam_active_confs += 1
		else:
			if self.damage_beam_active_confs == (0 - self.neg_required_confs):
				if self.damage_beam:
					self.damage_beam = False
			else:
				if self.damage_beam_active_confs > 0:
					self.damage_beam_active_confs = -1
				else:
					self.damage_beam_active_confs -= 1

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
			self.refresh()
			counter += 1
		print(f"Per second: {counter/seconds}")
		print(f"Average time: {round(1000 * (seconds/counter), 4)}ms")

#player = Player(isMercy=True)
#time.sleep(3)
#player.refresh()
#player.benchmark(1)
#player.benchmark(10)
#player.benchmark(100)
#player.per_sec(10)
