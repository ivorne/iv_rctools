#pragma once

#include "Types.hpp"

std::pair< GlyphInfo, Bitmap_RGB > loadMsdfBitmap( uint32_t code, FT_Face face, float MsdfPixelRange, int msdf_font_size, int border );
