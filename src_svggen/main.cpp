#include <msdfgen.h>
#include <msdfgen-ext.h>

#include <map>
#include <sstream>
#include <iostream>
#include <iostream>
#include <fstream>

bool ExportSvg( const char * input_filename, const char * output_filename, float pixel_range )
{
	//-------- load shape --------
	msdfgen::Shape shape;
	msdfgen::Vector2 dimensions;
	if( !loadSvgShape( shape, input_filename, 0, &dimensions ) )
	{
		std::cerr << "Svg load failed." << std::endl;
		return false;
	}
	
	//------- process shape ------
	{
		shape.normalize();
		msdfgen::edgeColoringSimple( shape, 3.0 );
		
		if( !shape.validate() )
		{
			std::cerr << "Shape validation failed." << std::endl;
			return false;
		}
	}
	
	//---------- read dimensions ---------
	double l, b, r, t;
	shape.bounds( l, b, r, t );
	
	//float const msdf_border = 4.0f;
	
	std::cout << "msdf_svg dimensions: " << l << " " << b << " " << r << " " << t << std::endl;
	std::cout << "msdf_svg dims: " << dimensions.x << " " << dimensions.y << std::endl;
	
	//---------- rasterize --------------
	msdfgen::Bitmap< msdfgen::FloatRGB > bitmap( dimensions.x, dimensions.y );
	//msdfgen::Bitmap< msdfgen::FloatRGB > bitmap( 800, 800 );
	msdfgen::generateMSDF( bitmap, shape, pixel_range, msdfgen::Vector2( 1, 1 ), msdfgen::Vector2( 0.0f, 0.0f ), 1.00000001 );
	
	//---------- save bitmap --------------------
	msdfgen::savePng( bitmap, output_filename, true );
	
	return true;
}

int main( int argc, char ** argv )
{
	if( argc != 4 )
	{
		std::cout << "Usage: " << argv[ 0 ] << " IN_SVG OUT_PNG PIXEL_RANGE" << std::endl;
		return 1;
	}
	
	std::cout << "msdf_svg: " << argv[ 1 ] << " " << argv[ 2 ] << " " << atoi( argv[ 3 ] ) << std::endl;
	
	if( !ExportSvg( argv[ 1 ], argv[ 2 ], atoi( argv[ 3 ] ) ) )
		return -1;
	
	return 0;
}

