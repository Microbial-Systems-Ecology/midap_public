function execute = tracking_supersegger(path, constants, neighbor_flag, time_step, min_cell_age, data_type)

	% set default values for parameters
	if isequal(time_step, 'None')
		time_step = 1;
	end

	if isequal(neighbor_flag, 'None')
		neighbor_flag = true;
	end

	if isequal(min_cell_age, 'None')
		min_cell_age = 3;
	end
	
	% add path
	addpath(genpath('../SuperSegger'))
	addpath(genpath(path))

	% define folder with images
	image_folder = path

	% set constants for segmentation and tracking
	PARALLEL_FLAG = false
	CONST = loadConstants (constants,PARALLEL_FLAG); %'60XEclb' '100XPa' '100XEc'
	CONST.getLocusTracks.TimeStep = time_step;%1;
	CONST.trackOpti.NEIGHBOR_FLAG = neighbor_flag; %true;
	CONST.trackOpti.MIN_CELL_AGE = min_cell_age; %3; %1%3

	% set default parameters for tracking
	CONST.parallel.verbose = 0;
	CONST.trackOpti.REMOVE_STRAY = false;

	if isequal(data_type, 'WELL')
		CONST.trackOpti.MIN_AREA_NO_NEIGH = 8;
		CONST.trackOpti.SMALL_AREA_MERGE = 8;
		CONST.getLocusTracks.PixelSize = 6/162;
	end
	

	%CONST.trackLoci.numSpots = [0];
	%CONST.superSeggerOpti.MAX_SEG_NUM = 100000;
	%CONST.regionOpti.MAX_NUM_RESOLVE = 100000;
	%CONST.findFocusSR.MAX_TRACE_NUM = 100000;
	%CONST.trackOpti.REMOVE_STRAY = true;
	%CONST.trackOpti.MIN_AREA = 30; %0;
	%CONST.trackOpti.MIN_AREA_NO_NEIGH = 30; %0;
	%CONST.trackOpti.MIN_CELL_AGE = 3;
	%CONST.trackOpti.REMOVE_STRAY = true;
	%CONST.trackLoci.numSpots = [5];
	

	% run only tracking
	clean_flag = 1; %0 
	startEnd = [3 10] %[3 10]
	BatchSuperSeggerOpti(image_folder,1,clean_flag,CONST,startEnd,0);
	execute = 0;
	exit;
end

