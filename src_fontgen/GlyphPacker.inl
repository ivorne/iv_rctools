#pragma once

template< class BT >
std::pair< std::vector< GlyphInfo >, msdfgen::Bitmap<BT> > packGlyphs( std::vector< std::pair< GlyphInfo, msdfgen::Bitmap<BT> > > glyphs, int BorderPx, BT border_fill )
{
	// compute area
	float area = 0.0f;
	for( auto glyph : glyphs )
		area += glyph.first.width * glyph.first.height;
	
	// sort glyphs by height
	std::sort( glyphs.begin(), glyphs.end(), 
		[]( std::pair< GlyphInfo, msdfgen::Bitmap<BT> > const & l, std::pair< GlyphInfo, msdfgen::Bitmap<BT> > const & r )
		{
			return std::tie( l.first.height, l.first.width, l.first.code )
				 > std::tie( r.first.height, r.first.width, r.first.code );
		}
	);
	
	// decide on glyph aggregation
	unsigned size = std::log( area ) * 1.44269f;
	bool packed = false;
	while( !packed )
	{
		packed = true;
		unsigned x = BorderPx;
		unsigned y = BorderPx;
		unsigned row_height = 0;
		
		for( auto const & glyph : glyphs )
		{
			// go to next line?
			if( x + glyph.first.width + BorderPx > size )
			{
				x = BorderPx;
				y += row_height + BorderPx;
				row_height = 0;
				if( y > size )
				{
					packed = false;
					size++;
					break;
				}
			}
			
			// add to line
			x += glyph.first.width + BorderPx;
			row_height = std::max( row_height, glyph.first.height );
		}
		
		// finalize last line
		y += row_height + BorderPx;
		if( y > size )
		{
			packed = false;
			size++;
		}
	}		
	
	// unitialize target bitmap
	msdfgen::Bitmap<BT> bitmap( size, size );
	{
		for( size_t i = 0; i < size; i++ )
			for( size_t j = 0; j < size; j++ )
				bitmap( i, j ) = border_fill;
	}
	
	// aggregate glyphs
	std::vector< GlyphInfo > index;
	{
		unsigned x = BorderPx;
		unsigned y = BorderPx;
		unsigned row_height = 0;
		
		for( auto & glyph : glyphs )
		{
			// go to next line?
			if( x + glyph.first.width + BorderPx > size )
			{
				x = BorderPx;
				y += row_height + BorderPx;
				row_height = 0;
			}
			
			// write bitmap
			for( unsigned i = 0; i < glyph.first.width; i++ )
				for( unsigned j = 0; j < glyph.first.height; j++ )
					bitmap( x + i, y + j ) = glyph.second( i, j );
			
			// modify info
			glyph.first.pos_x = x;
			glyph.first.pos_y = y;
			
			// copy info
			index.push_back( glyph.first );
			
			// next
			x += glyph.first.width + BorderPx;
			row_height = std::max( row_height, glyph.first.height );
		}
	}
	
	//
	return std::pair( index, bitmap );
}
