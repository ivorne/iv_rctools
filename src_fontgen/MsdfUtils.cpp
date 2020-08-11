#include "MsdfUtils.hpp"

#include <iostream>
using namespace std;

//-------------------------------------------------------------------------------
//-----------------

struct FtContext
{
    msdfgen::Point2 position;
    msdfgen::Shape *shape;
    msdfgen::Contour *contour;
};

static msdfgen::Point2 ftPoint2(const FT_Vector &vector)
{
    return msdfgen::Point2(vector.x/64.0f, vector.y/64.0f);
}

static int ftMoveTo(const FT_Vector *to, void *user)
{
    FtContext *context = reinterpret_cast<FtContext *>(user);
    context->contour = &context->shape->addContour();
    context->position = ftPoint2(*to);
    return 0;
}

static int ftLineTo(const FT_Vector *to, void *user)
{
    FtContext *context = reinterpret_cast<FtContext *>(user);
    context->contour->addEdge(new msdfgen::LinearSegment(context->position, ftPoint2(*to)));
    context->position = ftPoint2(*to);
    return 0;
}

static int ftConicTo(const FT_Vector *control, const FT_Vector *to, void *user)
{
    FtContext *context = reinterpret_cast<FtContext *>(user);
    context->contour->addEdge(new msdfgen::QuadraticSegment(context->position, ftPoint2(*control), ftPoint2(*to)));
    context->position = ftPoint2(*to);
    return 0;
}

static int ftCubicTo(const FT_Vector *control1, const FT_Vector *control2, const FT_Vector *to, void *user)
{
    FtContext *context = reinterpret_cast<FtContext *>(user);
    context->contour->addEdge(new msdfgen::CubicSegment(context->position, ftPoint2(*control1), ftPoint2(*control2), ftPoint2(*to)));
    context->position = ftPoint2(*to);
    return 0;
}
//---------------------------------------------------------------------------
//---------------------------------------------------------------------------
std::pair< GlyphInfo, Bitmap_RGB > loadMsdfBitmap( uint32_t code, FT_Face face, float MsdfPixelRange, int msdf_font_size, int border )
{
	//------- load FT glyph ------
	{
		FT_Error error = FT_Load_Char( face, code, FT_LOAD_NO_SCALE );
		if( error )
		{
			cerr << "loadGlyph(): FT_Load_Char failed for utf8 code " << code << ": FT_Error " << error << endl;
			return std::pair< GlyphInfo, Bitmap_RGB >();
		}
	}
	
	//------- create shape -----------
	msdfgen::Shape shape;
	{
		shape.inverseYAxis = true;

		FtContext context = {};
		context.shape = &shape;
		
		FT_Outline_Funcs ftFunctions;
		ftFunctions.move_to = &ftMoveTo;
		ftFunctions.line_to = &ftLineTo;
		ftFunctions.conic_to = &ftConicTo;
		ftFunctions.cubic_to = &ftCubicTo;
		ftFunctions.shift = 0;
		ftFunctions.delta = 0;
		
		FT_Error error = FT_Outline_Decompose( &face->glyph->outline, &ftFunctions, &context );
		if( error )
		{
			cerr << "loadMsdf(): FT_Outline_Decompose failed: FT_Error " << error << endl;
			return std::pair< GlyphInfo, Bitmap_RGB >();
		}
	}
	
	//------- process shape ------
	{
		shape.normalize();
		msdfgen::edgeColoringSimple( shape, 3.0 );
		
		if( !shape.validate() )
		{
			cerr << "loadMsdf(): msdfgen::Shape::validate failed." << endl;
			return std::pair< GlyphInfo, Bitmap_RGB >();
		}
	}
	
	//--------- some info ----------------
	float empu = 1.0f / face->units_per_EM * 64.0f;
	float scale = (float)msdf_font_size * empu;
	
	//
	GlyphInfo info;
	{
		info.code = code;
		info.pos_x = 0;
		info.pos_y = 0;
		
		auto metrics = face->glyph->metrics;
		info.width = 2 * border + std::ceil( metrics.width / 64.0f * scale );
		info.height = 2 * border + std::ceil( metrics.height / 64.0f * scale );
		info.bearing_x = - border + metrics.horiBearingX / 64.0f * scale;
		info.bearing_y = border + metrics.horiBearingY / 64.0f * scale;
		info.advance = metrics.horiAdvance / 64.0f * scale;
	}
	
	//---------- rasterize --------------
	Bitmap_RGB bitmap( info.width, info.height );
	{
		float empu = 1.0f / face->units_per_EM;
		float scale = (float)msdf_font_size * empu * 64.0f;
		msdfgen::generateMSDF( bitmap, shape, MsdfPixelRange / scale, msdfgen::Vector2( scale, scale ), msdfgen::Vector2( - info.bearing_x / scale,  - ( info.bearing_y - info.height ) / scale ), 1.00000001 );
	}
	
	//---------------
	return std::pair( info, bitmap );
}
