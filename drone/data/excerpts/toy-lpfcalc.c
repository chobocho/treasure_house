// silver13/h8mini-dual H8mini_test/src/util.c @a34d221f0c32ece06d4009f9cdfb71193fb51b58 L34-58 · MIT · fetched 2026-09-25
float lpfcalc(float sampleperiod, float filtertime)
{
	if (sampleperiod <= 0)
		return 0;
	if (filtertime <= 0)
		return 1;
	float ga = expf(-1.0f / ((1.0f / sampleperiod) * (filtertime)));
	if (ga > 1)
		ga = 1;
	return ga;
}

// arduino style map function
float mapf(float x, float in_min, float in_max, float out_min, float out_max)
{

	return ((x - in_min) * (out_max - out_min)) / (in_max - in_min) + out_min;

}

// simple lpf
void lpf(float *out, float in, float coeff)
{
	*out = (*out) * coeff + in * (1 - coeff);
}
