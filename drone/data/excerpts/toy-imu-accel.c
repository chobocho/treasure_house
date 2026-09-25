// silver13/h8mini-dual H8mini_test/src/imu.c @a34d221f0c32ece06d4009f9cdfb71193fb51b58 L229-261 · MIT · fetched 2026-09-25


// calc acc mag
	float accmag;

	accmag = calcmagnitude(&accel[0]);
		
	static unsigned int count = 0;

	if ((accmag > ACC_MIN * ACC_1G) && (accmag < ACC_MAX * ACC_1G) && !DISABLE_ACC)
	  {	
		  if (count >= 3 || 1)	//
		    {
						// normalize acc
					for (int axis = 0; axis < 3; axis++)
					{
						accel[axis] = accel[axis] * ( ACC_1G / accmag);
					}
			    float filtcoeff = lpfcalc(deltatime, FILTERTIME);
			    for (int x = 0; x < 3; x++)
			      {
				      lpf(&EstG[x], accel[x], filtcoeff);
			      }
		    }
		  count++;
	  }
	else
	  {			
			// acc mag out of bounds
		  count = 0;
	  }

	vectorcopy(&GEstG[0], &EstG[0]);
