// 슬라이드 p1-design-exc-ver — 라이브러리 1판: A 만 던진다, Java 21
public class Lib {
    public static void foo(int n) throws A {
        if (n == 0) throw new A();
        System.out.println("foo(" + n + ") ok");
    }
}
