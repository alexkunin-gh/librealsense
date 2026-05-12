// License: Apache 2.0. See LICENSE file in root directory.
// Copyright(c) 2025 RealSense, Inc. All Rights Reserved.

#include "rsutils/accelerators/gpu.h"
#include <rsutils/easylogging/easyloggingpp.h>

#ifdef _WIN32
#include <windows.h>
#else
#include <dlfcn.h>
#endif

namespace rsutils {

    // Probe whether a CUDA-capable GPU is usable on this machine.
    //
    // We dlopen / LoadLibrary the CUDA Driver library (libcuda.so.1 / nvcuda.dll) and
    // call cuInit(0) + cuDeviceGetCount().  This is deliberately decoupled from the
    // build-time RS2_USE_CUDA flag and from libcudart:
    //   - A binary built without CUDA can still detect a working GPU and surface a
    //     hint to rebuild for GPU acceleration.
    //   - A binary built with CUDA on Jetson can still load (and answer "no GPU here")
    //     on a system without the CUDA stack -- the function itself has no link-time
    //     dependency on libcuda / libcudart, so the dynamic linker does not fail at
    //     process startup.
    //
    // Both cuInit() and cuDeviceGetCount() are called: cuInit() alone returns success
    // when the driver loads, even with zero visible devices (e.g. CUDA_VISIBLE_DEVICES
    // is empty or all devices are masked).  Requiring count > 0 matches the prior
    // semantics of cudaGetDeviceCount() > 0.  Result is cached for the lifetime of
    // the process.
    //
    // Calling convention: CUDA's CUDAAPI macro is __stdcall on 32-bit Windows and is
    // a no-op on x64 Windows / POSIX.  Wrong convention on x86 would corrupt the
    // stack across the call.
    static bool probe_cuda_driver()
    {
#ifdef _WIN32
        using cu_init_t          = int ( __stdcall * )( unsigned int );
        using cu_device_count_t  = int ( __stdcall * )( int * );
        HMODULE handle = LoadLibraryA( "nvcuda.dll" );
        if( ! handle )
        {
            LOG_INFO( "CUDA driver library (nvcuda.dll) not found - GPU acceleration unavailable." );
            return false;
        }
        auto cu_init  = reinterpret_cast< cu_init_t         >( GetProcAddress( handle, "cuInit" ) );
        auto cu_count = reinterpret_cast< cu_device_count_t >( GetProcAddress( handle, "cuDeviceGetCount" ) );
#else
        using cu_init_t          = int ( * )( unsigned int );
        using cu_device_count_t  = int ( * )( int * );
        void * handle = dlopen( "libcuda.so.1", RTLD_LAZY );
        if( ! handle )
        {
            LOG_INFO( "CUDA driver library (libcuda.so.1) not found - GPU acceleration unavailable." );
            return false;
        }
        auto cu_init  = reinterpret_cast< cu_init_t         >( dlsym( handle, "cuInit" ) );
        auto cu_count = reinterpret_cast< cu_device_count_t >( dlsym( handle, "cuDeviceGetCount" ) );
#endif

        int count = 0;
        bool init_ok       = cu_init && cu_init( 0 ) == 0;
        bool count_ok      = init_ok && cu_count && cu_count( &count ) == 0;
        bool have_device   = count_ok && count > 0;

#ifdef _WIN32
        FreeLibrary( handle );
#else
        dlclose( handle );
#endif

        if( have_device )
            LOG_INFO( "CUDA driver detected with " << count << " visible device(s) - GPU acceleration available." );
        else if( ! init_ok )
            LOG_INFO( "CUDA driver library loaded but cuInit failed - GPU acceleration unavailable." );
        else if( ! count_ok )
            LOG_INFO( "CUDA driver initialised but cuDeviceGetCount failed - GPU acceleration unavailable." );
        else
            LOG_INFO( "CUDA driver initialised but zero visible devices - GPU acceleration unavailable." );
        return have_device;
    }

    bool rs2_is_cuda_available()
    {
        static bool const cached = probe_cuda_driver();
        return cached;
    }

} // namespace rsutils
