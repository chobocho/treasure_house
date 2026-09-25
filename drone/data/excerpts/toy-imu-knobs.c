// silver13/h8mini-dual H8mini_test/src/imu.c @a34d221f0c32ece06d4009f9cdfb71193fb51b58 L22-34 · MIT · fetched 2026-09-25
#define ACC_1G 2048.0f

// disable drift correction ( for testing)
#define DISABLE_ACC 0

// filter time in seconds
// time to correct gyro readings using the accelerometer
// 1-4 are generally good
#define FILTERTIME 2.0

// accel magnitude limits for drift correction
#define ACC_MIN 0.7f
#define ACC_MAX 1.3f
