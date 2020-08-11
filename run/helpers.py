import os
import re
import helpers
import json

_project_root = None
_rctools_path = None
_dir_src = None
_dir_tgt = None
_build_dir = None

_rcfiles = None
_toolfile = None

_compilation_index = None
_active_inputs = None
_metadata = None

_preserved_outfiles = { ".rctools_index", "metadata.json", ".gitkeep" }

#---------------- misc -------------------------------------------------------
def each_file( dir=".", rexp=r"", recursive=False ):
    for file in os.listdir( dir ):
        filepath = os.path.join( dir, file )
        if os.path.isfile( filepath ):
            if ( rexp == r'\.rc\.py$' ) or not re.search(r'\.rc\.py$',file):
                if re.search(rexp, file):
                    yield filepath
        elif recursive and os.path.isdir( filepath ):
            yield from each_file( filepath, rexp, recursive )

def makedirs_for_file( outfile ):
	dirname = os.path.dirname( outfile )
	if not os.path.isdir( dirname ):
		os.makedirs( dirname )

#---------------- used from run.py ---------------------------------------------
def roots( dir_src ):
	helpers._dir_src = dir_src

def init( project_root, build_dir, dir_tgt ):
	helpers._project_root = project_root
	helpers._dir_tgt = dir_tgt
	helpers._build_dir = build_dir
	helpers._rctools_path = os.path.dirname( os.path.realpath(__file__) )
	helpers._rcfiles = []
	for rcfile in helpers.each_file( dir=helpers._rctools_path, rexp=r'\.py$', recursive=True ):
		helpers._rcfiles.append( rcfile )

def read_compilation_index():
	index_path = os.path.join( _dir_tgt, ".rctools_index" )
	if not os.path.isfile( index_path ):
		helpers._compilation_index = {}
	else:
		with open( index_path ) as index_file: 
			index_string = index_file.read() 
			helpers._compilation_index = json.loads( index_string )
	
	helpers._active_inputs = []

def read_metadata():
	metadata_path = os.path.join( _dir_tgt, "metadata.json" )
	if not os.path.isfile( metadata_path ):
		helpers._metadata = {}
	else:
		with open( metadata_path ) as metadata_file: 
			metadata_string = metadata_file.read() 
			helpers._metadata = json.loads( metadata_string )

def clear_inactive_infiles():
	for infile in list( helpers._compilation_index.keys() ):
		if infile not in helpers._active_inputs:
			del helpers._compilation_index[ infile ]

def delete_inactive_outfiles():
	outfiles = set()
	for infile in helpers._compilation_index.keys():
		for outfile in helpers._compilation_index[ infile ]:
			if outfile in outfiles:
				raise Exception( "It seems like at least two input resources generate the same output resource file '"+helpers._rel_outfile( outfile )+"'." )
			outfiles.add( outfile )
	
	for file in each_file( helpers._dir_tgt, recursive=True ):
		if file not in outfiles:
			relname = helpers._rel_outfile( file )
			if relname not in helpers._preserved_outfiles:
				# some checks to be extra sure we are not deleting data outside of our directory
				if os.path.commonprefix( [ file, helpers._dir_tgt ] ) != helpers._dir_tgt:
					raise Exception( "Critical error in rctools. Output file being deleted is not inside of output directory. File: "+file+", outdir: "+helpers._dir_tgt+"." )
				
				# check if there are symlinks in the path
				path = file
				prev = None
				while prev != path:
					if os.path.islink( path ):
						raise Exception( "I don't feel comfortable removing files in symlinks." )
					prev = path
					path = os.path.dirname( path )
				
				print( "DEL " + file )
				os.remove( file )

def tool_init( toolfile ):
	helpers._toolfile = os.path.abspath( toolfile )

def write_compilation_index():
	index_path = os.path.join( _dir_tgt, ".rctools_index" )
	with open( index_path, 'w' ) as index_file:
		index_string = json.dumps( helpers._compilation_index )
		index_file.write( index_string )

def close_metadata():
	# gather active outfiles
	outfiles = set()
	for infile in helpers._compilation_index.keys():
		for outfile in helpers._compilation_index[ infile ]:
			outfiles.add( "/"+helpers._rel_outfile( outfile ) )
	
	# remove inactive outfiles from metadata
	for file in list( helpers._metadata.keys() ):
		if file not in outfiles:
			del helpers._metadata[ file ]
	
	# save metadata to file
	metadata_path = os.path.join( _dir_tgt, "metadata.json" )
	with open( metadata_path, 'w' ) as metadata_file:
		metadata_string = json.dumps( helpers._metadata )
		metadata_file.write( metadata_string )

#-------------------- used from tools.py --------------------------------------------------
def get_project_root():
	return helpers._project_root

def get_rctools_path():
	return helpers._rctools_path

def get_build_dir_path():
	return helpers._build_dir

def get_destination( infile ):
	"""
	  Takes path (or path fraction) within input directory and transforms it into equivalent path relative to output directory.
	"""
	
	abs_infile = os.path.abspath( infile )
	
	if os.path.commonprefix( [ abs_infile, helpers._dir_src ] ) != helpers._dir_src:
		raise Exception( "Input file is not inside of input directory. Infile: "+abs_infile+", inroot: "+helpers._dir_src+"." )
	
	rel = os.path.relpath( infile, helpers._dir_src )
	outfile = os.path.join( helpers._dir_tgt, rel )
	
	return outfile


def rel_outfile( outfile ):
	return _rel_outfile( outfile )

def mark_active_inputs( infiles ):
	"""
	  Call this each time buildscripts are called.
	  Marks input files as being used (their output files will be preserved in output directory) and checks, if resource should be recompiled.
	  :param infiles: Iterable object with strings with names of input files.
	  :return: Bool - if the file should be recompiled (list of output files is unknown or output files are outdated).
	"""
	
	# mark inputs as active
	for infile in infiles:
		helpers._active_inputs.append( infile )
	
	# outfiles
	outfiles = []
	
	# find all outfiles
	for infile in infiles:
		if infile not in helpers._compilation_index:
			return True
		for outfile in helpers._compilation_index[ infile ]:
			outfiles.append( outfile )
	outfiles.append( os.path.join( helpers._dir_tgt, "metadata.json" ) )
	
	# find newest infile timestamp
	newest_infile_time = 0
	for infile in infiles:
		newest_infile_time = max( newest_infile_time, helpers._timestamp( infile ) )
		
	for rcfile in helpers._rcfiles:
		newest_infile_time = max( newest_infile_time, helpers._timestamp( rcfile ) )
	
	newest_infile_time = max( newest_infile_time, helpers._timestamp( helpers._toolfile ) )
	
	# find oldest outfile timestamp
	oldest_outfile_time = None
	for outfile in outfiles:
		if oldest_outfile_time == None:
			oldest_outfile_time = helpers._timestamp( outfile )
		else:
			oldest_outfile_time = min( oldest_outfile_time, helpers._timestamp( outfile ) )
	
	# we can't decide on rebuild time if not outfiles exist - so rebuild every time
	if oldest_outfile_time == None:
		return True
	
	# rebuild if newest infile is newer than outputs
	return newest_infile_time > oldest_outfile_time

def log_compilation( tool_name, main_infile ):
	"""
	  Call this when recompiling, before compilation (so that it is logged before it starts compiling).
	  :param tool_name: Name of the tool that processes the file, string.
	  :param main_infile: One of the input files, string.
	"""
	print( tool_name + " " + helpers._rel_infile( main_infile ) + "..." )

def mark_changed_inputs( infiles, outfiles ):
	"""
	  Call this when recompiling resource.
	  This informs compilation_index about which output files belong to input files of this resource.
	  This mapping allows us to check if input files should be recompiled and which output files should be preserved in output directory.
	  :param infiles: Iterable object with strings with names of input files.
	  :param outfiles: Iterable object with strings with names of output files.
	"""
	
	normalized_outfiles = []
	for outfile in outfiles:
		helpers._check_outfile( outfile )
		normalized_outfiles.append( outfile )
	
	for infile in infiles:
		helpers._compilation_index[ str( infile ) ] = normalized_outfiles

def add_metadata( outfile, file_class, metadata ):
	"""
	  Call this when recompiling resource.
	  This adds and entry to be written to resource metadata file.
	  This file can be used by the game to get list of resources and read some basic metadata about a resource (image width, height, etc.).
	  Should be called even when no specific metadata are available - the fact that the file exists is considered part of the metadata.
	  :param outfile: File in output directory with given metadata.
	  :param file_class: String name of resource type (can be used by the Game to tell which metadata entries to expect).
	  :param metadata: Dictionary with pairs name -> value. Both will be converted to strings and written to metadata file.
	"""
	print( "    -> " + file_class + " " + helpers._rel_outfile( outfile ) );
	
	helpers._check_outfile( outfile );
	
	# convert keys and values to strings
	normalized_metadata = {}
	normalized_metadata[ "class" ] = file_class
	for key in metadata.keys():
		normalized_metadata[ str( key ) ] = str( metadata[ key ] )
	
	# modify
	#helpers._metadata[ "/" + helpers._rel_outfile( outfile ) ] = normalized_metadata
	
	#print( "/"+helpers._rel_outfile( outfile ) )
	
	helpers._metadata[ "/" + helpers._rel_outfile( outfile ) ] = normalized_metadata

def warning( w ):
	print( "    warning: "+str( w ) )

#---------------- private -------------------------------
def _timestamp( file ):
	exists = os.path.isfile( file ) or os.path.isdir( file )
	if not exists:
		return 0
	
	return os.path.getmtime( file )

def _rel_infile( infile ):
	abs_infile = os.path.abspath( infile )
	rel_infile = os.path.relpath( abs_infile, helpers._dir_src )
	return rel_infile

def _rel_outfile( outfile ):
	helpers._check_outfile( outfile )
	abs_outfile = os.path.abspath( outfile )
	rel_outfile = os.path.relpath( abs_outfile, helpers._dir_tgt )
	return rel_outfile

def _check_outfile( outfile ):
	abs_outfile = os.path.abspath( outfile )
	if os.path.commonprefix( [ abs_outfile, helpers._dir_tgt ] ) != helpers._dir_tgt:
		raise Exception( "Output file is not inside of output directory. Outfile: "+abs_outfile+", outdir: "+helpers._dir_tgt+"." )





