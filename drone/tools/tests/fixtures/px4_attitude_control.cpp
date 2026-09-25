/**
 * @file AttitudeControl.cpp
 */

#include <AttitudeControl.hpp>

#include <mathlib/math/Functions.hpp>

using namespace matrix;

static __attribute__((noinline)) Quatf qmul(const Quatf &a, const Quatf &b) { return a * b; }
static __attribute__((noinline)) Quatf qinv(const Quatf &q) { return q.inversed(); }
static __attribute__((noinline)) Vector3f qzaxis(const Quatf &q) { return q.dcm_z(); }

void AttitudeControl::setProportionalGain(const matrix::Vector3f &proportional_gain, const float yaw_weight)
{
	_proportional_gain = proportional_gain;
	_yaw_w = math::constrain(yaw_weight, 0.f, 1.f);

	// compensate for the effect of the yaw weight rescaling the output
	if (_yaw_w > 1e-4f) {
		_proportional_gain(2) /= _yaw_w;
	}
}

void AttitudeControl::setRefModelFrequency(float omega_n)
{
	_omega_n = math::max(omega_n, 0.1f);
	_kq      = _omega_n * _omega_n;
}

void AttitudeControl::setAttitudeSetpoint(const Quatf &qd, const float yawspeed_setpoint, const float dt)
{
	Quatf qd_normalized = qd;
	qd_normalized.normalize();

	if (_ref_initialized && dt > 0.f) {
		propagateReferenceModel(qd_normalized, yawspeed_setpoint, dt);

	} else {
		// First call (or dt out of range): snap reference to the current setpoint.
		_q_ref = qd_normalized;
		_omega_correction.zero();
		_omega_command.zero();
		_ref_initialized = true;
	}
}

void AttitudeControl::propagateReferenceModel(const Quatf &qd, const float yawspeed_setpoint, const float dt)
{
	// 2nd-order critically damped ref model with exact (ZOH) discretisation.
	// Repeated eigenvalue at s = -_omega_n; unconditionally stable for any dt.

	// Tangent-space inputs: rotate the analytical yaw rate into q_ref's body
	//    frame, and form the small-angle error vector from q_ref to q_d.
	const Quatf q_ref_inv = qinv(_q_ref);
	const Vector3f yaw_axis_body = qzaxis(q_ref_inv); // world yaw axis expressed in q_ref's body frame
	const Vector3f omega_command = PX4_ISFINITE(yawspeed_setpoint)
				       ? yaw_axis_body * yawspeed_setpoint
				       : Vector3f{};

	Quatf q_err = qmul(q_ref_inv, qd);
	q_err.canonicalize();
	const Vector3f e = 2.f * q_err.imag();

	// Entries of exp(A*dt) for A = [0 -1; _kq -2*_omega_n]. A has the repeated eigenvalue lambda = -_omega_n.
	// The matrix N = A - lambda*I is then nilpotent (a matrix is nilpotent when
