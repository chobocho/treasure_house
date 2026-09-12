package compresslib;

import java.util.Arrays;

/**
 * zlib 과 gzip 컨테이너 — SPEC §10.8 (RFC 1950, RFC 1952).
 *
 * <p>gzip 머리의 MTIME 을 <b>0 으로 못 박는다.</b> 진짜 gzip 은 파일의
 * 수정 시각을 적어서 같은 입력에 같은 바이트가 안 나온다 — 재현이 안
 * 된다.
 */
public final class Containers {
  public static final int ZLIB_CMF = 0x78;  // CM 8 = deflate, CINFO 7
  // (CMF<<8|FLG) 가 31 의 배수여야 한다
  public static final int ZLIB_FLG = 0x9C;
  public static final int GZIP_DEFLATE = 8;
  public static final int GZIP_OS_UNKNOWN = 255;

  private Containers() {}

  public static byte[] zlibCompress(byte[] src) {
    ByteBuf out = new ByteBuf();
    out.push(ZLIB_CMF);
    out.push(ZLIB_FLG);
    out.extend(Deflate.deflateRaw(src));
    int a = Checksums.adler32(src);
    for (int i = 3; i >= 0; i--) {
      out.push((a >>> (8 * i)) & 0xFF);
    }
    return out.bytes();
  }

  public static byte[] zlibDecompress(byte[] src) {
    if (src.length < 6) {
      throw new CodecException("zlib 스트림이 너무 짧다");
    }
    int cmf = src[0] & 0xFF;
    int flg = src[1] & 0xFF;
    if ((cmf & 0x0F) != 8) {
      throw CodecException.of("zlib CM 이 8 이 아니다: %d", cmf & 0x0F);
    }
    if (((cmf << 8) | flg) % 31 != 0) {
      throw new CodecException(
          "zlib 머리의 검사식이 31 로 안 나눠진다");
    }
    if ((flg & 0x20) != 0) {
      throw new CodecException(
          "미리 정한 사전(FDICT)은 지원하지 않는다");
    }
    byte[] body = Arrays.copyOfRange(src, 2, src.length - 4);
    byte[] out = Inflate.inflateRaw(body);
    int want = 0;
    for (int i = src.length - 4; i < src.length; i++) {
      want = (want << 8) | (src[i] & 0xFF);
    }
    if (Checksums.adler32(out) != want) {
      throw new CodecException("Adler-32 가 다르다");
    }
    return out;
  }

  public static byte[] gzipCompress(byte[] src) {
    ByteBuf out = new ByteBuf();
    int[] head = {0x1F, 0x8B, GZIP_DEFLATE, 0,
        0, 0, 0, 0, 0, GZIP_OS_UNKNOWN};
    for (int b : head) {
      out.push(b);
    }
    out.extend(Deflate.deflateRaw(src));
    int c = Checksums.crc32(src);
    int n = src.length;
    for (int i = 0; i < 4; i++) {
      out.push((c >>> (8 * i)) & 0xFF);
    }
    for (int i = 0; i < 4; i++) {
      out.push((n >>> (8 * i)) & 0xFF);
    }
    return out.bytes();
  }

  public static byte[] gzipDecompress(byte[] src) {
    if (src.length < 18) {
      throw new CodecException("gzip 스트림이 너무 짧다");
    }
    if ((src[0] & 0xFF) != 0x1F || (src[1] & 0xFF) != 0x8B) {
      throw new CodecException("gzip 매직이 아니다");
    }
    if ((src[2] & 0xFF) != GZIP_DEFLATE) {
      throw CodecException.of("gzip CM 이 8 이 아니다: %d",
          src[2] & 0xFF);
    }
    int flg = src[3] & 0xFF;
    int pos = 10;
    if ((flg & 0x04) != 0) {      // FEXTRA
      pos += 2 + ((src[pos] & 0xFF) | ((src[pos + 1] & 0xFF) << 8));
    }
    for (int bit : new int[] {0x08, 0x10}) {    // FNAME, FCOMMENT
      if ((flg & bit) != 0) {
        while (pos < src.length && src[pos] != 0) {
          pos++;
        }
        pos++;
      }
    }
    if ((flg & 0x02) != 0) {      // FHCRC
      pos += 2;
    }
    if (pos + 8 >= src.length) {
      throw new CodecException("gzip 머리가 잘렸다");
    }
    byte[] body = Arrays.copyOfRange(src, pos, src.length - 8);
    byte[] out = Inflate.inflateRaw(body);
    int base = src.length - 8;
    int crc = 0;
    int size = 0;
    for (int i = 3; i >= 0; i--) {
      crc = (crc << 8) | (src[base + i] & 0xFF);
      size = (size << 8) | (src[base + 4 + i] & 0xFF);
    }
    if (Checksums.crc32(out) != crc) {
      throw new CodecException("CRC-32 가 다르다");
    }
    if (out.length != size) {
      throw new CodecException("ISIZE 가 푼 길이와 다르다");
    }
    return out;
  }
}
