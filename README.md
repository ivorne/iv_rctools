# Ivorium rctools
Resource compilation tools for ivorium game developmenet framework.

## Requirements
  - python3
  - freetype library
  - GIMP (`gimp-console`)

## Usage
Include it in your CMakeLists.txt file and call function *iv_rctools_target* to create CMake target *resources*.

Here *game* is our main target that links to *ivorium*.
```cmake
# add custom directory with resources
set_property( TARGET game PROPERTY IVORIUM_RESOURCES_DIR ${CMAKE_CURRENT_SOURCE_DIR}/resources )

# build only on HOST platform
if( CMAKE_SYSTEM_NAME MATCHES ${CMAKE_HOST_SYSTEM_NAME} )
  # add iv_rctools subdirectory
  add_subdirectory( "modules/iv_rctools" )

  # add resources target
  iv_rctools_target( resources ${CMAKE_CURRENT_BINARY_DIR}/data game )

  # create dependency of resources on our main target
  add_dependencies( game resources )
endif()
```
