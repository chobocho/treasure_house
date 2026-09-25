// mavlink/c_library_v2 checksum.h @27ffe84e79d2e025c9bf6ccd1637f352e49a151b L22-55 · MIT (MAVLink 생성 코드) · fetched 2026-09-25
#define X25_INIT_CRC 0xffff
#define X25_VALIDATE_CRC 0xf0b8

#ifndef HAVE_CRC_ACCUMULATE
/**
 * @brief Accumulate the CRC16_MCRF4XX checksum by adding one char at a time.
 *
 * The checksum function adds the hash of one char at a time to the
 * 16 bit checksum (uint16_t).
 *
 * @param data new char to hash
 * @param crcAccum the already accumulated checksum
 **/
static inline void crc_accumulate(uint8_t data, uint16_t *crcAccum)
{
        /*Accumulate one byte of data into the CRC*/
        uint8_t tmp;

        tmp = data ^ (uint8_t)(*crcAccum &0xff);
        tmp ^= (tmp<<4);
        *crcAccum = (*crcAccum>>8) ^ (tmp<<8) ^ (tmp <<3) ^ (tmp>>4);
}
#endif


/**
 * @brief Initialize the buffer for the MCRF4XX CRC16
 *
 * @param crcAccum the 16 bit MCRF4XX CRC16
 */
static inline void crc_init(uint16_t* crcAccum)
{
        *crcAccum = X25_INIT_CRC;
}
