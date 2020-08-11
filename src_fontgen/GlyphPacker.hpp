#pragma once

#include <algorithm>
#include <tuple>

template< class BT >
std::pair< std::vector< GlyphInfo >, msdfgen::Bitmap<BT> > packGlyphs( std::vector< std::pair< GlyphInfo, msdfgen::Bitmap<BT> > > glyphs, int BorderPx, BT border_fill );

#include "GlyphPacker.inl"
