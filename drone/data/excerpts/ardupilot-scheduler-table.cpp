// ArduPilot/ardupilot ArduCopter/Copter.cpp @9f648ccabcf25a421192dc5b57491ce981506872 L115-154 · GPL-3.0 · fetched 2026-09-25
    FAST_TASK_CLASS(AP_InertialSensor, &copter.ins, update),
    // run low level rate controllers that only require IMU data
    FAST_TASK(run_rate_controller_main),
#if AC_CUSTOMCONTROL_MULTI_ENABLED
    FAST_TASK(run_custom_controller),
#endif
#if FRAME_CONFIG == HELI_FRAME
    FAST_TASK(heli_update_autorotation),
#endif //HELI_FRAME
    // send outputs to the motors library immediately
    FAST_TASK(motors_output_main),
     // run EKF state estimator (expensive)
    FAST_TASK(read_AHRS),
#if FRAME_CONFIG == HELI_FRAME
    FAST_TASK(update_heli_control_dynamics),
#endif //HELI_FRAME
    // Inertial Nav
    FAST_TASK(read_inertia),
    // check if ekf has reset target heading or position
    FAST_TASK(check_ekf_reset),
    // run the attitude controllers
    FAST_TASK(update_flight_mode),
    // update home from EKF if necessary
    FAST_TASK(update_home_from_EKF),
    // check if we've landed or crashed
    FAST_TASK(update_land_and_crash_detectors),
    // surface tracking update
    FAST_TASK(update_rangefinder_terrain_offset),
#if HAL_MOUNT_ENABLED
    // camera mount's fast update
    FAST_TASK_CLASS(AP_Mount, &copter.camera_mount, update_fast),
#endif
#if HAL_LOGGING_ENABLED
    FAST_TASK(Log_Video_Stabilisation),
#endif

    SCHED_TASK(rc_loop,              250,    130,  3),
    SCHED_TASK(throttle_loop,         50,     75,  6),
#if AP_FENCE_ENABLED
    SCHED_TASK(fence_check,           25,    100,  7),
