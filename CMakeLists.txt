cmake_minimum_required( VERSION 3.10 )

#-------- project ---------------------------------------------------
project( iv_rctools )

set( CMAKE_CXX_STANDARD 17 )
set( CMAKE_CXX_STANDARD_REQUIRED True )

#-------- msdfgen ----------------------------------------------------
add_subdirectory( libs/msdfgen EXCLUDE_FROM_ALL )

#-------- fontgen ----------------------------------------------------
file(
	GLOB_RECURSE cpp_SOURCES
	LIST_DIRECTORIES false
	CONFIGURE_DEPENDS
	"src_fontgen/*.cpp"
)

add_executable( fontgen "${cpp_SOURCES}" )
set_target_properties( fontgen PROPERTIES OUTPUT_NAME fontgen )
target_include_directories( fontgen PUBLIC "src_fontgen" )
target_include_directories( fontgen PUBLIC "libs/msdfgen" )
target_include_directories( fontgen PUBLIC "libs/msdfgen/include" )
target_link_libraries( fontgen lib_msdfgen )

#-------- svggen ----------------------------------------------------
file(
	GLOB_RECURSE cpp_SOURCES
	LIST_DIRECTORIES false
	CONFIGURE_DEPENDS
	"src_svggen/*.cpp"
)

add_executable( svggen "${cpp_SOURCES}" )
set_target_properties( svggen PROPERTIES OUTPUT_NAME svggen )
target_include_directories( svggen PUBLIC "src_svggen" )
target_include_directories( svggen PUBLIC "libs/msdfgen" )
target_include_directories( svggen PUBLIC "libs/msdfgen/include" )
target_link_libraries( svggen lib_msdfgen )

#------------- resources function -----------------------------------
set( RCTOOLS_SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR} PARENT_SCOPE )
set( RCTOOLS_BUILD_DIR ${CMAKE_CURRENT_BINARY_DIR} PARENT_SCOPE )

macro( iv_rctools_append_resdirs variable_name input_target )
	
	# process dependencies
	get_property( TGTS_DEFINED TARGET ${input_target} PROPERTY LINK_LIBRARIES SET )
	if( TGTS_DEFINED )
		get_property( TGTS TARGET ${input_target} PROPERTY LINK_LIBRARIES )
		foreach( TGT IN LISTS TGTS )
			
			if( TARGET ${TGT} )
				get_property( TYPE TARGET ${TGT} PROPERTY TYPE )
				if( NOT TYPE STREQUAL INTERFACE_LIBRARY )
					iv_rctools_append_resdirs( ${variable_name} ${TGT} )
				endif()
			endif()
			
		endforeach()
	endif()
	
	# add resource dir from input_target
	get_property( RESDIR_DEFINED TARGET ${input_target} PROPERTY IVORIUM_RESOURCES_DIR SET )
	if( RESDIR_DEFINED )
		get_property( RESDIR TARGET ${input_target} PROPERTY IVORIUM_RESOURCES_DIR )
		if( NOT RESDIR IN_LIST ${variable_name} )
			set( ${variable_name} ${${variable_name}} ${RESDIR} )
		endif()
	endif()
	
endmacro()

function( iv_rctools_target target_name destination_path input_target )
	
	set( RESDIRS )
	iv_rctools_append_resdirs( RESDIRS ${input_target} )
	message( STATUS "resdirs: ${RESDIRS}" )
	
	add_custom_target(
		${target_name}
		COMMAND python3 ${RCTOOLS_SOURCE_DIR}/run/run.py ${RCTOOLS_BUILD_DIR} ${destination_path} - ${RESDIRS}
	)
	add_dependencies( ${target_name} fontgen )
	add_dependencies( ${target_name} svggen )
endfunction()
