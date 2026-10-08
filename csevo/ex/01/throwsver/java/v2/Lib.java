// 슬라이드 p1-design-exc-ver — 라이브러리 2판: D 를 더한다, Java 21
public class Lib {
    public static void foo(int n) throws A, D {
        if (n == 0) throw new A();
        if (n < 0) throw new D();
        System.out.println("foo(" + n + ") ok");
    }
}
