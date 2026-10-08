// 슬라이드 p1-net-il — 바이트코드의 add 는 형식마다 다르다, Java 21
public class Add {
    static int addI(int a, int b) { return a + b; }
    static long addL(long a, long b) { return a + b; }
    static double addD(double a, double b) { return a + b; }
}
