// ArduPilot/ardupilot libraries/AC_AttitudeControl/AC_AttitudeControl.cpp @e4b7c11761da3c4547030c202beb7b55bec6279b L1064-1103 · GPL-3.0 · fetched 2026-09-25
    const Vector3f att_target_thrust_vec = attitude_target * thrust_vector_up; // target thrust vector

    // Rotating [0,0,-1] by attitude_target expresses (gets a view of) the current thrust vector in the inertial frame
    const Vector3f att_body_thrust_vec = attitude_body * thrust_vector_up; // current thrust vector

    // the dot product is used to calculate the current lean angle for use of external functions
    thrust_angle_rad = acosf(constrain_float(thrust_vector_up * att_body_thrust_vec,-1.0f,1.0f));

    // the cross product of the desired and target thrust vector defines the rotation vector
    Vector3f thrust_vec_cross = att_body_thrust_vec % att_target_thrust_vec;

    // the dot product is used to calculate the angle between the target and desired thrust vectors
    thrust_error_angle_rad = acosf(constrain_float(att_body_thrust_vec * att_target_thrust_vec, -1.0f, 1.0f));

    // Normalize the thrust rotation vector
    float thrust_vector_length = thrust_vec_cross.length();
    if (is_zero(thrust_vector_length) || is_zero(thrust_error_angle_rad)) {
        thrust_vec_cross = thrust_vector_up;
    } else {
        thrust_vec_cross /= thrust_vector_length;
    }

    // thrust_vector_correction is defined relative to the body frame but its axis `thrust_vec_cross` was computed in
    // the inertial frame. First rotate it by the inverse of attitude_body to express it back in the body frame
    thrust_vec_cross = attitude_body.inverse() * thrust_vec_cross;
    thrust_vector_correction.from_axis_angle(thrust_vec_cross, thrust_error_angle_rad);

    // calculate the angle error in x and y.
    Vector3f rotation_rad;
    thrust_vector_correction.to_axis_angle(rotation_rad);
    attitude_error_rad.x = rotation_rad.x;
    attitude_error_rad.y = rotation_rad.y;

    // calculate the remaining rotation required after thrust vector is rotated transformed to the body frame
    // heading_vector_correction
    Quaternion heading_vec_correction_quat = thrust_vector_correction.inverse() * attitude_body.inverse() * attitude_target;

    // calculate the angle error in z (x and y should be zero here).
    heading_vec_correction_quat.to_axis_angle(rotation_rad);
    attitude_error_rad.z = rotation_rad.z;
