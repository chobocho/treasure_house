// silver13/h8mini-dual H8mini_test/src/control.c @a34d221f0c32ece06d4009f9cdfb71193fb51b58 L142-164 · MIT · fetched 2026-09-25
	if (auxchange[HEADLESSMODE])
	  {
		  yawangle = 0;
	  }

	if ((aux[HEADLESSMODE]) )
	  {
		yawangle = yawangle + gyro[2] * looptime;

		while (yawangle < -3.14159265f)
    yawangle += 6.28318531f;

    while (yawangle >  3.14159265f)
    yawangle -= 6.28318531f;

		float temp = rxcopy[0];
		rxcopy[0] = rxcopy[0] * fastcos( yawangle) - rxcopy[1] * fastsin(yawangle );
		rxcopy[1] = rxcopy[1] * fastcos( yawangle) + temp * fastsin(yawangle ) ;
	  }
	else
	  {
		  yawangle = 0;
	  }
