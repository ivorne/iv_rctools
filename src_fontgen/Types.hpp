#pragma once

#include <utility>

#include <cstdint>

#include <msdfgen.h>
#include <msdfgen-ext.h>

#include <ft2build.h>
#include FT_FREETYPE_H
#include FT_OUTLINE_H

//#ifdef _WIN32
//    #pragma comment(lib, "freetype.lib")
//#endif

struct Range
{
	uint32_t begin;
	uint32_t end;
	
	Range() : begin( 0 ), end( 0 ){}
	Range( uint32_t begin, uint32_t end ) : begin( begin ), end( end ){}
};

struct FontInfo
{
	float line_height;
	float ascender;
	float descender;
	float max_advance;
};

using Bitmap_RGB = msdfgen::Bitmap< msdfgen::FloatRGB >;
using Bitmap_Mono = msdfgen::Bitmap< float >;

struct GlyphInfo
{
	uint32_t code;		// glyph (unicode code)
	unsigned pos_x;		// x position of glyph in bitmap (from left of image to left of glyph, in texture pixels)
	unsigned pos_y;		// y position of glyph in bitmap (from top of image to top of glyph, in texture pixels)
	unsigned width;		// width of glyph in pixels (from left of glyph to right of glyph, in texture pixels)
	unsigned height;	// height of glyph in pixels (from top of glyph to bottom of glyph, in texture pixels)
	float bearing_x;	// from base of glyph to left side of glyph, in texture pixels
	float bearing_y;	// from base of glyph to top side of glyph, in texture pixels
	float advance;		// advance of glyph, in texture pixels
};
