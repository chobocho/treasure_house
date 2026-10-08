// 슬라이드 p1-design-del-call — Sun 이 든 리플렉션 호출, Java 21
import java.lang.reflect.Method;

public class Main {
    public static int add(int a, int b) { return a + b; }

    public static void main(String[] args) throws Exception {
        Method m = Main.class.getMethod("add", int.class, int.class);
        Object r = m.invoke(null, 3, 4);   // 3 and 4 become Integers
        System.out.println(r + " " + r.getClass().getName());
    }
}
