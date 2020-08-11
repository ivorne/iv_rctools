import helpers
import os
import sys

def init( build_dir, dir_tgt ):
	print( "binary_dir: "+os.path.abspath( build_dir ) )
	print( "output_dir: "+os.path.abspath( dir_tgt ) )
	
	helpers.init( os.path.abspath( os.getcwd() ), os.path.abspath( build_dir ), os.path.abspath( dir_tgt ) )
	helpers.read_compilation_index()
	helpers.read_metadata()

def run( dir_src ):
	print( "input_dir:  "+os.path.abspath( dir_src ) )
	
	helpers.roots( os.path.abspath( dir_src ) )
	
	# run all rc scripts
	cwd = os.getcwd()
	for file in helpers.each_file( dir=dir_src, rexp=r'\.rc\.py$', recursive=True ):
		with open( file ) as f:
			helpers.tool_init( file )
			os.chdir( os.path.dirname( file ) )
			code = compile( f.read(), file, 'exec' );
			exec( code );
			os.chdir( cwd )

def close():
	print( "close" )
	
	# finalize
	helpers.clear_inactive_infiles()
	helpers.delete_inactive_outfiles()
	helpers.write_compilation_index()
	helpers.close_metadata()
	
	print( "done" )
	
#run( sys.argv[ 1 ], sys.argv[ 2 ] )

dir_tgt = None
first = True
second = True
build_dir = None
for param in sys.argv:
	if first:
		first = False
	elif second:
		second = False
		build_dir = param
	elif param[ 0 ] != "-":
		if not dir_tgt:
			dir_tgt = param
			init( build_dir, dir_tgt )
		else:
			run( param )

if dir_tgt:
	close()
