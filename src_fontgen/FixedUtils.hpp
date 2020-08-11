#pragma once

#include "Types.hpp"

std::pair< GlyphInfo, Bitmap_Mono > loadFixedBitmap( uint32_t code, FT_Face face, int size );
