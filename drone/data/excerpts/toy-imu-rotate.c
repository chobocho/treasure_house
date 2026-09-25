// silver13/h8mini-dual H8mini_test/src/imu.c @a34d221f0c32ece06d4009f9cdfb71193fb51b58 L211-226 · MIT · fetched 2026-09-25
#ifdef SMALL_ANGLE_APPROX

	float deltaGyroAngle = (gyro[0]) * deltatime;
	EstG[2] = scos(deltaGyroAngle) * EstG[2] - ssin(deltaGyroAngle) * EstG[0];
	EstG[0] = ssin(deltaGyroAngle) * EstG[2] + scos(deltaGyroAngle) * EstG[0];

	deltaGyroAngle = (gyro[1]) * deltatime;
	EstG[1] = scos(deltaGyroAngle) * EstG[1] + ssin(deltaGyroAngle) * EstG[2];
	EstG[2] = -ssin(deltaGyroAngle) * EstG[1] + scos(deltaGyroAngle) * EstG[2];

	deltaGyroAngle = (gyro[2]) * deltatime;
	EstG[0] = scos(deltaGyroAngle) * EstG[0] - ssin(deltaGyroAngle) * EstG[1];
	EstG[1] = ssin(deltaGyroAngle) * EstG[0] + scos(deltaGyroAngle) * EstG[1];

#endif				// end small angle approx

