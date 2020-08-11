#include "FixedUtils.hpp"
#include <iostream>
using namespace std;


std::pair< GlyphInfo, Bitmap_Mono > loadFixedBitmap( uint32_t code, FT_Face face, int size )
{
	bool const Antialiasing = true;
	
	//------- select size --------
	{
		FT_Error error = FT_Set_Char_Size( face, size << 6, size << 6, 0, 0 );	// dpi 0 defaults to 72
		if( error )
		{
			cerr << "loadGlyph(): FT_Load_Char failed for utf8 code " << code << ": FT_Error " << error << endl;
			return std::pair< GlyphInfo, Bitmap_Mono >();
		}
	}
	
	//---------- load glyph ---------
	{
		auto err = FT_Load_Glyph( face, FT_Get_Char_Index( face, code ), Antialiasing ? FT_LOAD_FORCE_AUTOHINT : FT_LOAD_DEFAULT );	//  to turn off antialiasing
		if(err)
		{
			cerr << "loadFont(): FT_Load_Glyph failed for utf8 code " << code << ": FT_Error " << err << endl;;
			return std::pair< GlyphInfo, Bitmap_Mono >();
		}
	}

	//----------- render glyph ----------------
	{
		if( Antialiasing )
			FT_Render_Glyph( face->glyph, FT_RENDER_MODE_NORMAL );
		else
			FT_Render_Glyph( face->glyph, FT_RENDER_MODE_MONO );
	}
	
	
	//-----
	if( face->glyph->bitmap.width != face->glyph->metrics.width / 64 )
		cerr << "Bitmap width does not match metrics' width." << endl;
	if( face->glyph->bitmap.rows != face->glyph->metrics.height / 64 )
		cerr << "Bitmap rows count does not match metrics' width." << endl;
	
	//---------------
	Bitmap_Mono result;
	{
		FT_Bitmap& bitmap = face->glyph->bitmap;
		int width  = bitmap.width;
		int height = bitmap.rows;
		
		if( width != 0 && height != 0 )
		{
			if( Antialiasing )
			{
				result = Bitmap_Mono( width, height ); 
				for( int x = 0; x < width; x++ )
					for( int y = 0; y < height; y++ )
						result( x, y ) = bitmap.buffer[ y * width + x ] / 255.0f;
			}
			else
			{
				cerr << "copy glyph bitmap is unimplemented without antialiasing" << endl;
				return std::pair< GlyphInfo, Bitmap_Mono >();
			}
		}
	}
	
	//
	GlyphInfo info;
	{
		info.code = code;
		info.pos_x = 0;
		info.pos_y = 0;
		
		auto metrics = face->glyph->metrics;
		info.width = metrics.width / 64.0f;
		info.height = metrics.height / 64.0f;
		info.bearing_x = metrics.horiBearingX / 64.0f;
		info.bearing_y = metrics.horiBearingY / 64.0f;
		info.advance = metrics.horiAdvance / 64.0f;
	}
	
	return std::pair( info, result );
}
