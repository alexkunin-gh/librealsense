// License: Apache 2.0. See LICENSE file in root directory.
// Copyright(c) 2026 RealSense, Inc. All Rights Reserved.

#pragma once

#ifdef BUILD_WITH_MINZ

#include <librealsense2/rs.hpp>
#include <memory>
#include "min-z-depth-improver.h"

// rs2::filter adapter for min_z_depth_improver.
// Plugs directly into the per-sensor post_processing chain so it can be
// positioned relative to temporal / spatial / hole-filling by the user.
// Upstream depth filters (temporal, spatial) never touch IR frames, so the
// frameset arriving here carries original IR alongside the already-filtered
// depth — exactly what DepthRangeImprover needs.
class minz_filter : public rs2::filter
{
    std::shared_ptr< min_z_depth_improver > _improver;

    // Private delegating ctor: receives the already-constructed shared_ptr so
    // the lambda can capture it by value before the base rs2::filter is init'd.
    // This avoids capturing 'this': the lambda keeps _improver alive independently
    // of the minz_filter object's lifetime.
    explicit minz_filter( std::shared_ptr< min_z_depth_improver > imp )
        : rs2::filter( [imp]( rs2::frame f, rs2::frame_source & src )
            {
                src.frame_ready( imp->apply( f, src ) );
            } )
        , _improver( imp )
    {}

public:
    minz_filter() : minz_filter( std::make_shared< min_z_depth_improver >() ) {}
};

#endif  // BUILD_WITH_MINZ
