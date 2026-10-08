// 슬라이드 p1-design-exc-java — 검사 예외: 잡거나 선언하거나, Java 21
import java.io.IOException;

public class Main {
    static String load(String path) throws IOException {
        throw new IOException("cannot open " + path);
    }

    public static void main(String[] args) {
        System.out.println(load("a.txt"));
    }
}
