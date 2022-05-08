

class ZwoCamera:
	"""ZwoCamera is an abstraction layer for zwoasi Python bindings"""

	mode = None

	@staticmethod
	def initialize(library=None):
		if library is None:
			library = os.path.dirname(os.path.realpath(__file__)) + "/asi.so"
		asi.init(library)

	@staticmethod
	def cameras():
		return asi.list_cameras()

	def _get_default(self, prop):
		return None if prop not in self.camera_properties else self.camera_properties[prop].get("DefaultValue", None)

	@staticmethod
	def sigalrm_watchdog(signum, frame):
		raise TimeoutError("Caught SIGALRM waiting for exposure to complete")

	def __init__(self, camera_id=None, bandwidth=80, use_sigalrm_watchdog=False):
		"Initialize self.camera to a default good state"
		logger.debug("Creating Camera")
		self.camera = asi.Camera(camera_id)
		self.camera.stop_video_capture()
		self.camera.stop_exposure()

		if use_sigalrm_watchdog:
			signal.signal(signal.SIGALRM, ZwoCamera.sigalrm_watchdog)
		else:
			signal.signal(signal.SIGALRM, signal.SIG_IGN)

		logger.debug("Getting camera info")
		self.camera_info = self.camera.get_camera_property()

		logger.debug("Getting camera controls")
		self.camera_properties = self.camera.get_controls()

		self.name = self.camera_info.get("Name", "").lower().replace(" ", "_")
		self.camera.set_control_value(asi.ASI_BANDWIDTHOVERLOAD, bandwidth)

		self.configure(
			gain=self._get_default("Gain"),
			exposure=self._get_default("Exposure"),
			flip=self._get_default("Flip"),
			wb_b=self._get_default("WB_B"),
			wb_r=self._get_default("WB_R"),
			color=True if self._get_default("WB_R") else False,
			drange=8,
			bitdepth=self._get_default("Bitdepth"),
			gamma=self._get_default("Gamma"),
			binning=self.camera_info["SupportedBins"][0],
		)
		self.camera.start_video_capture()

	def configure(
		self,
		*,
		gain=None,
		exposure=None,
		wb_b=None,
		wb_r=None,
		gamma=None,
		offset=None,
		flip=None,
		binning=None,
		roi=None,
		drange=None,
		bitdepth=None,
		color=None,
		mode=None,
	):
		"""Used to change camera parameters

		Args:
			gain (int): Camera gain
			exposure (int): Camera exposure in microseconds
			wb_b (int): Camera whitebalance
			wb_r (int): Camera whitebalance
			gamma (int): Camera gamma
			offset (int): Camera brightness
			flip (int): Picture flip, valuse can be 0 or 1
			binning (int): Picture binning, values can be 1 or 2
			roi (tuple): Region of interest, formatted as a tuple (x, y, width, height)
			drange (int): Dynamic range, value can be 8 or 16 bits
			bitdepth (int): 8, 16, or 24 bits
			color (bool): Camera color mode
			mode (str): Capturing mode, value can be 'video' or 'picture'
		"""

		self.camera.stop_video_capture()
		self.camera.stop_exposure()

		if exposure is not None:
			self.camera.set_control_value(asi.ASI_EXPOSURE, exposure)
		if gain is not None:
			self.camera.set_control_value(asi.ASI_GAIN, gain)
		if wb_b is not None:
			self.camera.set_control_value(asi.ASI_WB_B, wb_b)
		if wb_r is not None:
			self.camera.set_control_value(asi.ASI_WB_R, wb_r)
		if gamma is not None:
			self.camera.set_control_value(asi.ASI_GAMMA, gamma)
		if offset is not None:
			self.camera.set_control_value(asi.ASI_OFFSET, offset)
		if flip is not None:
			if flip == "horizontal":
				flip = 1
			elif flip == "vertical":
				flip = 2
			elif flip == "both":
				flip = 3
			else:
				flip = 0
			self.camera.set_control_value(asi.ASI_FLIP, flip)

		if binning is None:
			binning = 1

		if roi is None:
			roi = (0, 0, int(self.camera_info["MaxWidth"] / binning), int(self.camera_info["MaxHeight"] / binning))

		self.camera.set_roi(start_x=roi[0], start_y=roi[1], width=roi[2], height=roi[3], bins=binning)

		if color is True:
			self.camera.set_image_type(asi.ASI_IMG_RGB24)
		else:
			if drange == 8:
				self.camera.set_image_type(asi.ASI_IMG_RAW8)
			elif drange == 16:
				self.camera.set_image_type(asi.ASI_IMG_RAW16)

		if mode is not None:
			# self.mode = mode
			raise NotImplementedError("Capture mode selection not implemented")
		self.camera.start_video_capture()
		# if mode == "video":
		#	self.camera.start_video_capture()
		# elif mode == "picture":
		#	self.camera.stop_video_capture()

	def retryable_capture(self, num_retries=3, retry_delay=0.5):
		exptime = self.get_exposure_time()
		last_exception = None
		for i in range(num_retries):
			try:
				signal.alarm(round(exptime + 1))
				frame = self.camera.capture_video_frame()
				signal.alarm(0)
				return frame
			except KeyboardInterrupt:
				signal.alarm(0)
				self.camera.stop_video_capture()
				self.camera.stop_exposure()
				raise
			except asi.ZWO_Error as e:
				time.sleep(retry_delay)
				last_exception = str(e)
		raise asi.ZWO_IOError(last_exception)

	def get_temperature(self) -> float:
		"helper method to retrieve sensor temperature in 'C"
		return self.camera.get_control_value(asi.ASI_TEMPERATURE)[0] / 10

	def get_exposure_time(self) -> float:
		"helper method to retrieve exposure time in seconds"
		return self.camera.get_control_value(asi.ASI_EXPOSURE)[0] / 1e6

	def show_camera_info(self) -> None:
		from json import dumps

		tmp = dumps(self.camera_info, sort_keys=True, indent=2)
		print(f"\nCamera Info:{tmp}")

		tmp = dumps(self.camera_properties, sort_keys=True, indent=2)
		print(f"\nCamera Controls: {tmp}")

class ap_helpers:
	"Just some custom type validators for argparse"

	@staticmethod
	def bitdepth(s: str) -> int:
		i = int(s)
		if i != 8 and i != 16 and i != 24:
			raise ValueError("Bitdepth must be mono: 8 or 16.   color: 24")
		return i

	@staticmethod
	def gain(s: str) -> List[int]:
		fields = s.split(":")
		if len(fields) != 3:
			raise ValueError("Incorrect gain specification")
		rv = [int(x) for x in fields]
		if rv[0] < -2:
			raise ValueError("Invalid minimum gain")
		if rv[1] < -2 or rv[1] < rv[0]:
			raise ValueError("Invalid maxiumum gain")
		if rv[2] < -2 or rv[2] == 0:
			raise ValueError("Invalid gain step")
		return rv

	@staticmethod
	def exposure(s: str) -> List[float]:
		fields = s.split(":")
		if len(fields) != 3:
			raise ValueError("Incorrect exposure specification")
		rv = [float(x) for x in fields]
		if rv[0] < 1e-3:
			raise ValueError("Invalid minimum exposure (min 1ms)")
		if rv[1] > 900:
			raise ValueError("Invalid maximum exposure (max 900s)")
		if rv[2] < 1e-3:
			raise ValueError("Invalid exposure step (min 1ms)")
		return rv

	@staticmethod
	def non_neg_int(s: str) -> int:
		i = int(s)
		if i < 0:
			raise ValueError("Non-negative integer required")
		return i

	@staticmethod
	def pos_int(s: str) -> int:
		i = int(s)
		if i < 1:
			raise ValueError("Positive integer required")
		return i

	@staticmethod
	def img_size(s: str) -> Optional[Tuple[int]]:
		if s is None:
			return
		s = [ap_helpers.pos_int(i) for i in s.lower().split("x")]
		if len(s) != 2:
			raise ValueError("Size specification must be in the form <int>x<int>")

	@staticmethod
	def flip(s=None) -> int:
		flips = {"n": 0, "h": 1, "v": 2, "hv": 3, "vh": 3, "b": 3}
		if s is None:
			return list(flips.keys())
		return flips[s.lower()]


def get_args() -> argparse.Namespace:
	ep = """
	When constructing the output filename, the following tokens are available:
	{temp} - sensor temperature in C, rounded up: 26.1 -> 27;
	{gain} - gain in arbitrary units;
	{expms} - exposure time in milliseconds;
	{exps} - exposure time in integer seconds;
	{model} - sanitized camera model: 'ZWO ASI120MM Mini' -> 'zwo_asi120mm_mini';
	{stack} - stacking factor
	"""

	ap = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, epilog=ep)
	ap.add_argument("-c", "--camera", type=int, help="Camera index")
	ap.add_argument("-I", "--info", default=False, action="store_true", help="Print info about selected camera")
	ap.add_argument("-l", "--library", metavar="PATH", default="./libASICamera2.so", help="path to SDK library")
	ap.add_argument("-d", "--directory", metavar="PATH", help="path to output darks")
	ap.add_argument("-f", "--filename-format", metavar="STR", default="dark_{exps}s_{gain:03d}g_{temp:02d}C.png",
		help="filename pattern for darks. The tokens {model}, "
		"{stack}, {expms}, {exps}, {gain}, and {temp} will be interpolated as python formats.",
	)
	ap.add_argument("-b", "--bitdepth", metavar="INT", type=ap_helpers.bitdepth,
		help="bit depth: 8, 16, or 24 (color)",
	)
	ap.add_argument("-g", "--gain", metavar="MIN:MAX:STEP", default="-1:-1:-1", type=ap_helpers.gain,
		help="gain range to scan (int; -1=automatic)",
	)
	ap.add_argument("-x", "--exposure", metavar="MIN:MAX:STEP", default="2:20:2", type=ap_helpers.exposure,
		help="exposure range to scan, in seconds. (float)",
	)
	ap.add_argument("--binning", default=1, type=ap_helpers.pos_int, help="Pixel binning factor")
	ap.add_argument("--stack", default=1, metavar="INT", type=ap_helpers.pos_int,
		help="Number of exposures to stack to build dark frame",
	)
	ap.add_argument("--flip", type=ap_helpers.flip, choices=ap_helpers.flip(),
		help="flip image: none, horizonal, vertical, both"
	)
	ap.add_argument("--quality", default=100, type=ap_helpers.pos_int, help="image quality")
	ap.add_argument("--offset", default=0, metavar="INT", type=ap_helpers.non_neg_int, help="brightness offset")
	ap.add_argument("--wbr", metavar="INT", type=ap_helpers.pos_int, help="white balance: red")
	ap.add_argument("--wbb", metavar="INT", type=ap_helpers.pos_int, help="white balance: blue")
	# ap.add_argument("--size", type=ap_helpers.img_size)
	# ap.add_argument("--no-video", default=False, action="store_true")
	ap.add_argument("-v", "--verbose", default=0, action="count")
	return ap.parse_args()


def main():
	args = get_args()

	if args.verbose:
		loglevel = logging.DEBUG if args.verbose > 1 else logging.INFO
	else:
		loglevel = logging.WARNING
	logger.setLevel(loglevel)
	logging.basicConfig()

	logger.debug("Initializing Library")
	ZwoCamera.initialize(args.library)

	logger.debug("Detecting Cameras")
	camlist = [(i, c) for i, c in enumerate(ZwoCamera.cameras())]
	if not camlist:
		print("No cameras detected!")
		exit()

	if len(camlist) == 1:
		args.camera = 0
	elif args.camera is None:
		print("No camera specified. Select one of:")
		for c in camlist:
			print(f"	{c[0]:2d} -> {c[1]}")
		exit()

	zwocam = ZwoCamera(args.camera, use_sigalrm_watchdog=True)
	if args.info:
		zwocam.show_camera_info()
		exit()

	if args.bitdepth is None:
		print("\nERROR: Must specify a bit depth of 8, 16, or 24.\n")
		exit()

	# unless otherwise specified scan from 25-75% of gain range
	tmp = (zwocam.camera_properties["Gain"]["MinValue"] + zwocam.camera_properties["Gain"]["MaxValue"]) / 2
	if args.gain[0] == -1:
		args.gain[0] = round(tmp - tmp / 2)
	if args.gain[1] == -1:
		args.gain[1] = round(tmp + tmp / 2)
	if args.gain[2] == -1:
		args.gain[2] = round(tmp / 10)

	if args.exposure[1] == -1:
		args.exposure[1] = zwocam.camera_properties["Exposure"]["MaxValue"] // 1000
	if args.binning and args.binning not in zwocam.camera_info["SupportedBins"]:
		raise ValueError(f"Binning value must be one of {zwocam.camera_info['SupportedBins']}")

	if args.directory is None:
		args.directory = ""
	else:
		os.makedirs(args.directory, exist_ok=True)
	img_params = {"quality": args.quality, "subsampling": 0 if args.quality >= 100 else 1}

	for _ in range(5):
		zwocam.camera.capture_video_frame()

	# convert exposure to microseconds since that's what the library uses
	args.exposure = [int(s * 1e6) for s in args.exposure]

	exposure_list = list(range(args.exposure[0], args.exposure[1] + args.exposure[2], args.exposure[2]))
	gain_list = list(range(args.gain[0], args.gain[1] + 1, args.gain[2]))

	total_exp_time = len(gain_list) * sum(exposure_list) * args.stack * 1e-6
	num_exps = len(gain_list) * len(exposure_list) * args.stack
	total_storage = num_exps * zwocam.camera_info["MaxHeight"] * zwocam.camera_info["MaxWidth"]
	total_storage *= args.bitdepth/8

	print(f"This run will take approximately {total_exp_time/60:.1f}min.", end=" ")
	print(f"Estimated size {num_exps} files, {total_storage//1024**2}MB")
	if args.verbose:
		print(f"Scanning gain levels {gain_list}")
		print(f"Exposure durations {[round(x/1e6,1) for x in exposure_list]}")

	for exposure_us in exposure_list:
		for gain in gain_list:
			zwocam.configure(
				gain = gain,
				exposure = exposure_us,
				flip = args.flip,
				wb_b = args.wbb,
				wb_r = args.wbr,
				offset = args.offset,
				binning = args.binning,
				bitdepth = args.bitdepth,
			)
			images = []
			temperatures = []
			for i in range(args.stack):
				# sensor temperature may go up with exposure time, so measure it every exposure
				sensor_temp = zwocam.get_temperature()
				if args.verbose:
					print(f"\rn:{i:2d} exp:{exposure_us/1e6:.1f}s gain:{gain:3d} temp:{sensor_temp:+5.1f}'C", end="")
				images.append(zwocam.retryable_capture())
				temperatures.append(sensor_temp)
			temperatures.append(zwocam.get_temperature())

			# average the frames. maybe be more clever later
			# TODO: be much more clever and detect when the lens cap gets disturbed...
			stack_image = sum(images) / len(images)
			stack_image = Image.fromarray(stack_image.astype(uint8))
			# do normal round to match "capture" program: -39.99C -> -40C, 0.01C -> 0C
			stack_temperature = round(sum(temperatures) / len(temperatures))

			outfile = os.path.join(
				args.directory,
				args.filename_format.format_map(
					{
						"model": zwocam.name,
						"stack": args.stack,
						"gain": gain,
						"expms": exposure_us // 1000,
						"exps": int(exposure_us // 1000000),
						"temp": int(stack_temperature),
					}
				),
			)
			os.makedirs(os.path.dirname(outfile), exist_ok=True)
			if os.path.exists(outfile):
				os.unlink(outfile)
			stack_image.save(outfile, params=img_params)

	print("\nExposure sequence complete")


if __name__ == "__main__":
	main()
