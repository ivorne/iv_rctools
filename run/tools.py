import os
import helpers
import shutil
import PIL.Image
import subprocess

def image_validate( file ):
	im = PIL.Image.open( file )
	width, height = im.size
	if im.mode == 'RGBA':
		pixel_format = 'RGBA'
	else:
		im2 = im.convert( 'RGBA' )
		im2.save( file )
		pixel_format = 'RGBA'
	im.close()
	return { "width" : width, "height" : height, "pixel_format" : pixel_format }

def texture( file, density = 1.0, hitmap = False, instant_loading = False, filtering = "Nearest" ):
	infile = os.path.abspath( file )
	
	rebuild = helpers.mark_active_inputs( [ infile ] )
	
	if not rebuild:
		return
	
	outfile = helpers.get_destination( infile )
	helpers.log_compilation( "texture", infile )
	
	# build
	helpers.makedirs_for_file( outfile )
	shutil.copy( infile, outfile )
	
	imginfo = image_validate( outfile )
	
	# report build
	helpers.mark_changed_inputs( [ infile ], [ outfile ] )
	helpers.add_metadata( outfile, "texture", { **imginfo, "density" : density, "hitmap" : hitmap, "instant_loading" : instant_loading, "filtering" : filtering, "color_space" : "sRGB" } )


def msdf_svg( file, hitmap = False, instant_loading = False, msdf_pixelRange = 3.0 ):
	infile = os.path.abspath( file )
	
	rebuild = helpers.mark_active_inputs( [ infile ] )
	
	if not rebuild:
		return
	
	outfile = helpers.get_destination( infile )
	outfile = os.path.splitext( outfile )[ 0 ] + ".png"
	helpers.log_compilation( "msdf_svg", infile )
	
	# build
	helpers.makedirs_for_file( outfile )
	
	#
	density = 1.0
	msdf_pixel_range = msdf_pixelRange
	
	# run msdf_svg
	binary = os.path.join( helpers.get_build_dir_path(), "svggen" );
	process = subprocess.Popen( [ binary, infile, outfile, str( msdf_pixel_range ) ], stdout=subprocess.PIPE )
	stdout, stderr = process.communicate()
	
	print( stdout.decode( 'utf8' ) )
	
	if process.returncode:
		print( stderr.decode( 'utf8' ) )
		raise Exception( "msdf_svg failed" )
	
	# analyze metadata
	imginfo = image_validate( outfile )
	
	# report build
	helpers.mark_changed_inputs( [ infile ], [ outfile ] )
	helpers.add_metadata( outfile, "texture", { **imginfo, "density" : density, "hitmap" : hitmap, "instant_loading" : instant_loading, "filtering" : "SmoothMsdf", "msdf_pixelRange" : msdf_pixel_range, "color_space" : "linear" } )

def file( f, type_str ):
	infile = os.path.abspath( f )
	
	rebuild = helpers.mark_active_inputs( [ infile ] )
	
	if not rebuild:
		return
	
	outfile = helpers.get_destination( infile )
	helpers.log_compilation( str( type_str ), infile )
	
	# build
	helpers.makedirs_for_file( outfile )
	shutil.copy( infile, outfile )
	
	# report build
	helpers.mark_changed_inputs( [ infile ], [ outfile ] )
	helpers.add_metadata( outfile, str( type_str ), {} )

def wave( f ):
	file( f, "wave" )

def data( f ):
	file( f, "data" )

def font( file, instant_loading = False, msdf_pixelRange = 3.0, msdf_fontSize = 128 ):
	infile = os.path.abspath( file )
	
	rebuild = helpers.mark_active_inputs( [ infile ] )
	
	if not rebuild:
		return
	
	helpers.log_compilation( "font", infile )
	
	# make output directory
	outfile = helpers.get_destination( infile )
	outdir = os.path.splitext( outfile )[ 0 ] + "/"
	helpers.makedirs_for_file( outdir )
	
	# run fontgen
	fontgen = os.path.join( helpers.get_build_dir_path(), "fontgen" );
	process = subprocess.Popen( [ fontgen, infile, outdir, str( msdf_pixelRange ), str( msdf_fontSize ) ], stdout=subprocess.PIPE )
	stdout, stderr = process.communicate()
	
	if process.returncode:
		print( stdout.decode( 'utf8' ) )
		raise Exception( "Fontgen failed" )
	
	outfiles = []
	
	# report build
	for image in stdout.decode( 'utf8' ).split( '\n' ):
		if image == "":
			continue;
		
		image = image.strip()
		image = os.path.join( outdir, image )
		
		outfiles.append( image )
		
		# info
		imginfo = image_validate( image )
		
		# filtering
		if "msdf" in image:
			filtering = "SmoothMsdf"
		else:
			filtering = "Nearest"
		
		# density
		density = 1.0
		
		# metadata
		helpers.add_metadata( image, "texture", { **imginfo, "msdf_pixelRange" : msdf_pixelRange, "density" : density, "hitmap" : False, "instant_loading" : instant_loading, "filtering" : filtering, "color_space" : "linear" } )
	
	# index
	index = os.path.join( outdir, "font.index" )
	outfiles.append( index )
	helpers.add_metadata( index, "font", {} )
	
	# infiles -> outfiles mapping
	helpers.mark_changed_inputs( [ infile ], outfiles )

def xcf_layers( file, depth=1, density=1.0, hitmap = [], instant_loading = False, filtering = "Nearest", Nearest={} ):
	"""
		Export layers as images in directory named like the xcf file without the .xcf extension.
		:param depth: 1 means that root layers will be exported as separate images named as the layer name. 2 means that direct children of root layers will be exported, name of files will be root layer name followed by a dot followed by name of the child layer.
		:param hitmap_list: List of strings listing images for which a hitmap should be generated. Each image name is sequence of 'depth' layer names separated by a dot '.'.
	"""
	
	infile = os.path.abspath( file )
	
	rebuild = helpers.mark_active_inputs( [ infile ] )
	
	if not rebuild:
		return
	
	helpers.log_compilation( "xcf_layers", infile )
	
	# make output directory
	outfile = helpers.get_destination( infile )
	outdir = os.path.splitext( outfile )[ 0 ] + "/"
	helpers.makedirs_for_file( outdir )
	
	# run export
	script = "outdir = '"+outdir+"'\n"
	script += "max_depth = "+str( depth )+"\n"
	script += "density = "+str( density )+"\n"
	script += """
import os.path
with open( os.path.join( outdir, "xcf.info" ), 'w' ) as info:
	img = gimp.image_list()[ 0 ]
	info.write( 'width '+str( img.width )+'\\n' )
	info.write( 'height '+str( img.height )+'\\n' )

	#--- process layers ---
	info.write( '\\n' )
	info.write( '# global_order layer_name   width height    global_left global_right global_top global_bottom    local_left local_right local_top local_bottom\\n' )
	global_order = 1;
	def export_layer( img, layer, outfile ):
		pdb.file_png_save( img, layer, outfile, outfile, True, 5, True, True, True, True, True )
	
		#img_copy = pdb.gimp_image_duplicate( img )
		#for l in list( img_copy.layers ):
		#	if l.name != layer.name:
		#		img_copy.remove_layer( l )
		##layer_copy = img_copy.merge_visible_layers( 0 )
		##pdb.file_png_save( img_copy, layer_copy, outfile, outfile, True, 5, True, True, True, True, True )
		#pdb.gimp_image_resize_to_layers( img_copy )
		#pdb.file_png_save( img_copy, img_copy, outfile, outfile, True, 5, True, True, True, True, True )
		#pdb.gimp_image_delete( img_copy )
	
	def process_layer( layer, parent, parent_name, depth ):
		name = layer.name.split( "#" )[ 0 ].strip()
		if name == "":
			return
		
		if parent_name:
			name = parent_name + "." + name
		
		global_pos_left = layer.offsets[ 0 ]
		global_pos_right = img.width - layer.offsets[ 0 ] - layer.width
		global_pos_top = layer.offsets[ 1 ]
		global_pos_bottom = img.height - layer.offsets[ 1 ] - layer.height
		
		local_pos_left = global_pos_left;
		local_pos_right = global_pos_right;
		local_pos_top = global_pos_top;
		local_pos_bottom = global_pos_bottom;
		if parent:
			local_pos_left = layer.offsets[0] - parent.offsets[0]
			local_pos_right = parent.width - ( layer.offsets[0] - parent.offsets[0] ) - layer.width
			local_pos_top = layer.offsets[1] - parent.offsets[1]
			local_pos_bottom = parent.height - ( layer.offsets[1] - parent.offsets[1] ) - layer.height
		
		# write info
		global global_order
		info.write( 'layer '+str( global_order ) + ' "'+name+'"' )
		info.write( '    '+str( layer.width / density )+' '+str( layer.height / density ) )
		info.write( '    '+str( global_pos_left / density )+' '+str( global_pos_right / density )+' '+str( global_pos_top / density )+' '+str( global_pos_bottom / density ) )
		info.write( '    '+str( local_pos_left / density )+' '+str( local_pos_right / density )+' '+str( local_pos_top / density )+' '+str( local_pos_bottom / density ) )
		info.write( '\\n' )
		global_order += 1
		
		if type( layer ) == gimp.GroupLayer and depth < max_depth:
			# process children
			for sublayer in reversed( layer.layers ):
				process_layer( sublayer, layer, name, depth+1 )
		else:
			# render
			outfile = os.path.join( outdir, name+".png" )
			export_layer( img, layer, outfile )
			print( "98678542|LAYER "+name )
	
	for layer in reversed( img.layers ):
		process_layer( layer, None, None, 1 )

print( "SUCCESS_5896542" )
	"""
	
	command = [ "gimp-console", "-idf", "--batch-interpreter", "python-fu-eval", "-b", 'pdb.gimp_xcf_load(0,"'+str(infile)+'", "'+str(infile)+'")', "-b", script, "-b", "pdb.gimp_quit(1)", infile ]
	
	process = subprocess.Popen( command, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
	output, error = process.communicate()
	
	if "SUCCESS_5896542" not in output.decode( 'utf8' ):
		print( output.decode( 'utf8' ) )
		print( error.decode( 'utf8' ) )
		raise Exception( "Xcf compilation failed." )
	
	# gather all the created files
	layers = set()
	duplicits = set()
	for line in output.decode( 'utf8' ).splitlines():
		if "98678542|LAYER " in line:
			layer = line[ 15: ]
			if layer in layers:
				duplicits.add( layer )
			layers.add( layer )
	
	# images metadata
	for layer in layers:
		image = os.path.join( outdir, layer+".png" )
		
		imginfo = image_validate( image )
		
		img_filtering = filtering
		if layer in Nearest:
			img_filtering = "Nearest"
		helpers.add_metadata( image, "texture", { **imginfo, "density" : density, "hitmap" : ( layer in hitmap ), "instant_loading" : instant_loading, "filtering" : img_filtering, "color_space" : "sRGB" } )
	
	# infofile metadata
	infofile = os.path.join( outdir, "xcf.info" )
	helpers.add_metadata( infofile, "xcf", {} )
	
	# warning about diplicits
	for layer in duplicits:
		image = os.path.join( outdir, layer+".png" )
		helpers.warning( "Two images named "+helpers.rel_outfile( image )+" were created." )
	
	# infiles -> outfiles mapping
	outfiles = []
	for layer in layers:
		image = os.path.join( outdir, layer+".png" )
		outfiles.append( image )
	outfiles.append( infofile )
	helpers.mark_changed_inputs( [ infile ], outfiles )


def xcf( file, density=1.0, hitmap = False, instant_loading = False, filtering = "Nearest" ):
	"""
	  Just exports whole xcf file as png file, replacing .xcf extionsion with .png extension. Exapmle: MyImage.xcf -> MyImage.png.
	"""
	
	infile = os.path.abspath( file )
	
	rebuild = helpers.mark_active_inputs( [ infile ] )
	
	if not rebuild:
		return
	
	outfile = helpers.get_destination( infile )
	outfile = os.path.splitext( outfile )[ 0 ] + ".png"
	helpers.log_compilation( "xcf", infile )
	
	# makedirs
	helpers.makedirs_for_file( outfile )
	
	# export
	script = ""
	script += "outfile = '"+outfile+"'\n"
	script += "density = "+str( density )+"\n"
	script += """
img = gimp.image_list()[ 0 ]
layer = pdb.gimp_image_merge_visible_layers( img, 1 )
pdb.file_png_save( img, layer, outfile, outfile, True, 5, True, True, True, True, True )
print( "SUCCESS_5896542" )
"""
	
	command = [ "gimp-console", "-idf", "--batch-interpreter", "python-fu-eval", "-b", 'pdb.gimp_xcf_load(0,"'+str(infile)+'", "'+str(infile)+'")', "-b", script, "-b", "pdb.gimp_quit(1)", infile ]
	
	process = subprocess.Popen( command, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
	output, error = process.communicate()
	
	if "SUCCESS_5896542" not in output.decode( 'utf8' ):
		print( output.decode( 'utf8' ) )
		print( error.decode( 'utf8' ) )
		raise Exception( "Xcf compilation failed." )
	
	# metadata
	imginfo = image_validate( outfile )
	
	helpers.add_metadata( outfile, "texture", { **imginfo, "density" : density, "hitmap" : hitmap, "instant_loading" : instant_loading, "filtering" : filtering, "color_space" : "sRGB" } )
	
	# report outfile
	helpers.mark_changed_inputs( [ infile ], [ outfile ] )

