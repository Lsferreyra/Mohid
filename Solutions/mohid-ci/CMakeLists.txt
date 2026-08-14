cmake_minimum_required(VERSION 3.22)

project(MOHIDWater LANGUAGES C Fortran)

option(MOHID_ENABLE_MPI "Build MOHID Water with MPI support" OFF)
option(MOHID_ENABLE_OPENMP "Build MOHID Water with OpenMP support" OFF)
option(MOHID_ENABLE_NETCDF "Build MOHID Water with NetCDF support" OFF)
option(MOHID_RUNTIME_CHECKS "Enable compiler runtime checks" ON)
set(MOHID_INSTANCE_LIMIT "increased" CACHE STRING
    "MOHID instance table: standard (500), increased (2000), or extra (20000)")
set_property(CACHE MOHID_INSTANCE_LIMIT PROPERTY STRINGS standard increased extra)

set(MOHID_GIT_SHA "unknown" CACHE STRING "Git commit used for this build")
set(MOHID_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../.." CACHE PATH "MOHID repository root")
get_filename_component(MOHID_ROOT "${MOHID_ROOT}" ABSOLUTE)

if(MOHID_ENABLE_NETCDF)
    message(FATAL_ERROR
        "The first reproducible lane deliberately disables NetCDF. "
        "NetCDF will be enabled after compiler and HDF5 baselines pass.")
endif()

find_package(ZLIB REQUIRED)
set(HDF5_PREFER_PARALLEL OFF)
find_package(HDF5 REQUIRED COMPONENTS Fortran HL)

include(cmake/MohidWaterSources.cmake)

foreach(source IN LISTS MOHID_WATER_SOURCES)
    if(NOT EXISTS "${source}")
        message(FATAL_ERROR "MOHID source is missing: ${source}")
    endif()
endforeach()

add_executable(MohidWater ${MOHID_WATER_SOURCES})
set_target_properties(MohidWater PROPERTIES
    Fortran_MODULE_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/modules"
    OUTPUT_NAME "MohidWater.exe"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/bin"
)
set_source_files_properties(${MOHID_WATER_SOURCES} PROPERTIES Fortran_PREPROCESS ON)

target_compile_definitions(MohidWater PRIVATE
    _NO_NETCDF
    _LAGRANGIAN_GLOBAL_
    _USE_NIX
    _STACK_LIMITS_
    _BIG_LINE_LENGTH
)

if(MOHID_INSTANCE_LIMIT STREQUAL "increased")
    target_compile_definitions(MohidWater PRIVATE _INCREASE_MAXINSTANCES)
elseif(MOHID_INSTANCE_LIMIT STREQUAL "extra")
    target_compile_definitions(MohidWater PRIVATE _INCREASE_MAXINSTANCES_EXTRA)
elseif(NOT MOHID_INSTANCE_LIMIT STREQUAL "standard")
    message(FATAL_ERROR
        "MOHID_INSTANCE_LIMIT must be standard, increased, or extra; got "
        "'${MOHID_INSTANCE_LIMIT}'")
endif()

target_include_directories(MohidWater PRIVATE ${HDF5_INCLUDE_DIRS})
target_link_libraries(MohidWater PRIVATE
    ${HDF5_Fortran_HL_LIBRARIES}
    ${HDF5_Fortran_LIBRARIES}
    ${HDF5_HL_LIBRARIES}
    ${HDF5_LIBRARIES}
    ZLIB::ZLIB
    ${CMAKE_DL_LIBS}
    m
)

if(CMAKE_Fortran_COMPILER_ID STREQUAL "GNU")
    target_compile_options(MohidWater PRIVATE
        -cpp
        -fdefault-real-8
        -fdefault-double-8
        -fconvert=little-endian
        -ffree-line-length-none
        -ffixed-line-length-none
        -fallow-argument-mismatch
        -fno-unsafe-math-optimizations
        -frounding-math
        -fsignaling-nans
        -fPIC
    )
    if(MOHID_RUNTIME_CHECKS)
        target_compile_options(MohidWater PRIVATE
            -g3
            -fbacktrace
            -fcheck=all
            -ffpe-trap=invalid,zero,overflow
            -Wall
            -Wextra
            -Wimplicit-interface
            -Wno-unused-dummy-argument
            -Wno-tabs
        )
    endif()
elseif(CMAKE_Fortran_COMPILER_ID STREQUAL "IntelLLVM")
    target_compile_options(MohidWater PRIVATE
        -fpp
        -real-size 64
        -convert little_endian
        -heap-arrays 64
        -fp-model=source
        -fPIC
        -traceback
        -fpe0
    )
    if(MOHID_RUNTIME_CHECKS)
        target_compile_options(MohidWater PRIVATE -O0 -check all -warn all -stand f18)
    endif()
elseif(CMAKE_Fortran_COMPILER_ID STREQUAL "Intel")
    target_compile_options(MohidWater PRIVATE
        -fpp
        -real-size 64
        -convert little_endian
        -heap-arrays 64
        -fp-model source
        -fPIC
        -traceback
        -fpe0
    )
    if(MOHID_RUNTIME_CHECKS)
        target_compile_options(MohidWater PRIVATE -O0 -check all -warn all)
    endif()
else()
    message(FATAL_ERROR
        "Unsupported Fortran compiler '${CMAKE_Fortran_COMPILER_ID}'. "
        "The initial lanes support gfortran, ifx and ifort.")
endif()

if(MOHID_ENABLE_OPENMP)
    find_package(OpenMP REQUIRED COMPONENTS Fortran)
    target_link_libraries(MohidWater PRIVATE OpenMP::OpenMP_Fortran)
endif()

if(MOHID_ENABLE_MPI)
    find_package(MPI REQUIRED COMPONENTS Fortran)
    target_compile_definitions(MohidWater PRIVATE _USE_MPI)
    target_link_libraries(MohidWater PRIVATE MPI::MPI_Fortran)
endif()

file(GENERATE
    OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/mohid-build-info.txt"
    CONTENT
"git_sha=${MOHID_GIT_SHA}
fortran_compiler=${CMAKE_Fortran_COMPILER_ID} ${CMAKE_Fortran_COMPILER_VERSION}
build_type=${CMAKE_BUILD_TYPE}
hdf5_version=${HDF5_VERSION}
mpi=${MOHID_ENABLE_MPI}
openmp=${MOHID_ENABLE_OPENMP}
netcdf=${MOHID_ENABLE_NETCDF}
instance_limit=${MOHID_INSTANCE_LIMIT}
runtime_checks=${MOHID_RUNTIME_CHECKS}
")

install(TARGETS MohidWater RUNTIME DESTINATION bin)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/mohid-build-info.txt" DESTINATION share/mohid)
