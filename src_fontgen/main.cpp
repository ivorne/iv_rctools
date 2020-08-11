#include "Types.hpp"
#include "MsdfUtils.hpp"
#include "FixedUtils.hpp"
#include "GlyphPacker.hpp"

#include <map>
#include <sstream>
#include <iostream>
#include <iostream>
#include <fstream>
#include <algorithm>


using namespace std;

void serializeGlyphinfo( std::vector< GlyphInfo > const & glyphs, std::ostream & out )
{
	out << "\t # code   posx posy   width height   bearing_x bearing_y" << endl;
	for( auto const & glyph : glyphs )
	{
		out << "\t glyph " << glyph.code << "   "
			<< glyph.pos_x << " " << glyph.pos_y << "   "
			<< glyph.width << " " << glyph.height << "   "
			<< glyph.bearing_x << " " << glyph.bearing_y << endl;
	}
}

void loadKerning( FT_Face face, std::vector< Range > & Ranges, std::ostream & index )
{
	index << "kerning" << endl;
	index << "{" << endl;
	index << "\t # code_current, code_next, kerning" << endl;
	
	for( auto & range_current : Ranges )
		for( auto & range_next : Ranges )
			for( uint32_t code_current = range_current.begin; code_current < range_current.end; code_current++ )
				for( uint32_t code_next = range_next.begin; code_next < range_next.end; code_next++ )
				{
					// load kerning
					FT_Vector kerning;
					FT_Get_Kerning( face, code_current, code_next, FT_KERNING_DEFAULT, &kerning );
					
					//
					float empu = 1.0f / face->units_per_EM;
					float kerning_x = kerning.x * empu;
					float kerning_y = kerning.y * empu;
					
					// write to index
					if( kerning.x != 0 || kerning.y != 0 )
					{
						index << "\t kerning " << code_current << " " << code_next << " " << kerning_x << " " << kerning_y << endl;
					}
				}
	
	index << "}" << endl;
	index << endl;
}

void loadAdvances( FT_Face face, std::vector< Range > & Ranges, std::ostream & index )
{
	index << "advance" << endl;
	index << "{" << endl;
	index << "\t # code, advance, width" << endl;
	
	for( auto & range : Ranges )
		for( uint32_t code = range.begin; code < range.end; code++ )
		{
			//------- load FT glyph ------
			{
				FT_Error error = FT_Load_Char( face, code, FT_LOAD_NO_SCALE );
				if( error )
				{
					cerr << "loadGlyph(): FT_Load_Char failed for utf8 code " << code << ": FT_Error " << error << endl;
					return;
				}
			}
			
			//------ read advance ------
			float advance;
			float width;
			{
				auto metrics = face->glyph->metrics;
				float empu = 1.0f / face->units_per_EM;
				advance = metrics.horiAdvance * empu;
				width = std::max( 0.0f, ( metrics.width + metrics.horiBearingX ) * empu );
			}
			
			//---- write to index ----
			{
				index << "\t glyph " << code << " " << advance << " " << width << endl;
			}
		}
	
	index << "}" << endl;
	index << endl;
}

void loadMsdfFont( FT_Face face, std::vector< Range > & Ranges, float MsdfPixelRange, int msdf_font_size, std::string outdir, std::ostream & index )
{
	index << "variant msdf " << msdf_font_size << "    # size, pixelRange" << endl;
	index << "{" << endl;
	
	// config
	int const MsdfBorder = 4;
	int const PackingBorder = 2;
	
	// create glyphs
	std::vector< std::pair< GlyphInfo, Bitmap_RGB > > glyphs;
	for( auto & range : Ranges )
		for( uint32_t code = range.begin; code < range.end; code++ )
			glyphs.push_back( loadMsdfBitmap( code, face, MsdfPixelRange, msdf_font_size, MsdfBorder ) );
	
	// pack glyphs
	msdfgen::FloatRGB fill = { 0.0f, 0.0f, 0.0f };
	auto [ glyphinfo, bitmap ] = packGlyphs( glyphs, PackingBorder, fill );
	
	// save bitmap
	{
		std::stringstream ss;
		ss << outdir << "/msdf.png";
		msdfgen::savePng( bitmap, ss.str().c_str(), false );
		
		index << "\t texture \"./msdf.png\"" << endl;
		index << endl;
		
		cout << "msdf.png" << endl;
	}
	
	// save glyphinfo
	{
		serializeGlyphinfo( glyphinfo, index );
	}
	
	index << "}" << std::endl;
	index << std::endl;
}

void loadFixedFont( FT_Face face, std::vector< Range > & Ranges, int font_size, std::string outdir, std::ostream & index )
{
	index << "variant fixed " << font_size << "    # size" << endl;
	index << "{" << endl;
	
	// config
	int const PackingBorder = 1;
	
	// create glyphs
	std::vector< std::pair< GlyphInfo, Bitmap_Mono > > glyphs;
	for( auto & range : Ranges )
		for( uint32_t code = range.begin; code < range.end; code++ )
			glyphs.push_back( loadFixedBitmap( code, face, font_size ) );
	
	// pack glyphs
	float fill = 0.0f;
	auto [ glyphinfo, bitmap ] = packGlyphs( glyphs, PackingBorder, fill );
	
	// save bitmap
	{
		std::stringstream ss;
		ss << outdir << "/fixed_" << font_size << ".png";
		msdfgen::savePng( bitmap, ss.str().c_str(), false );
		
		index << "\t texture \"./fixed_" << font_size << ".png\"" << endl;
		index << endl;
		
		cout << "fixed_" << font_size << ".png" << endl;
	}
	
	// save glyphinfo
	{
		serializeGlyphinfo( glyphinfo, index );
	}
	
	index << "}" << std::endl;
	index << std::endl;
}

void PrerenderFont( const char * ttf_filepath, std::string outdir, float pixel_range, int msdf_font_size )
{
	//std::vector< int > FontSizes = { 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20 };
	std::vector< int > FontSizes = {};
	std::vector< Range > Ranges;
	//Ranges.push_back( Range( 71, 72 ) );			// G
	Ranges.push_back( Range( 32, 128 ) );			// Basic Latin
	Ranges.push_back( Range( 0x00A0, 0x0100 ) );	// Latin-1 Supplement
	Ranges.push_back( Range( 0x0100, 0x0180 ) );	// Latin Extended-A
	Ranges.push_back( Range( 0x0180, 0x0250 ) );	// Latin Extended-B
	Ranges.push_back( Range( 0x2500, 0x2580 ) );	// Box Drawing
	float const MsdfPixelRange = pixel_range;
	
	//----------- init ft handle -------------
	FT_Library ftHandle;
	{
		FT_Error error = FT_Init_FreeType( &ftHandle );
		if( error )
			cerr << "FtHandle(): FT_Init_FreeType failed: FT_Error " << error << endl;
	}
	
	//----------- load font ---------------------
	FT_Face face;
	{
		FT_Error error = FT_New_Face( ftHandle, ttf_filepath, 0, &face );
		if( error )
		{
			cerr << "load(): FT_New_Face failed with font '" << ttf_filepath << "': FT_Error " << error << endl;
			return;
		}
	}
	
	//--------- basic dimension info ---------
	FontInfo font_info;
	
	float empu = 1.0f / face->units_per_EM;
	//float scale = msdf_font_size * empu * 64.0f;
	
	font_info.line_height = face->height * empu;
	font_info.ascender = face->ascender * empu;
	font_info.descender = face->descender * empu;
	font_info.max_advance = face->max_advance_width * empu;
	
	//------ validate outdir --------
	if( outdir.size() == 0 )
		outdir = ".";
	
	//----------- index file ----------
	//cout << "font.index" << endl;
	
	std::stringstream index_filename;
	index_filename << outdir << "/font.index";
	std::ofstream index( index_filename.str().c_str() );
	
	index << "# geometry" << endl;
	index << "line_height " << font_info.line_height << endl;
	index << "ascender " << font_info.ascender << endl;
	index << "descender " << font_info.descender << endl;
	index << "max_advance " << font_info.max_advance << endl;
	index << endl;
	
	//------------- load glyphs --------------
	loadAdvances( face, Ranges, index );
	
	index << "# variants" << endl;
	
	loadMsdfFont( face, Ranges, MsdfPixelRange, msdf_font_size, outdir, index );
	
	for( auto size : FontSizes )
		loadFixedFont( face, Ranges, size, outdir, index );
	
	//index << "# kerning" << endl;
	//loadKerning( face, Ranges, index );
}

int main( int argc, char ** argv )
{
	if( argc != 5 )
	{
		std::cout << "Usage: " << argv[ 0 ] << " IN_TTF OUT_DIR PIXEL_RANGE MSDF_FONT_SIZE" << std::endl;
		return 1;
	}
	
	PrerenderFont( argv[ 1 ], argv[ 2 ], atof( argv[ 3 ] ), atoi( argv[ 4 ] ) );
	
	return 0;
}

