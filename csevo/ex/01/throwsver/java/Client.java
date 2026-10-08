// 슬라이드 p1-design-exc-ver — 1판에 맞춰 쓴 사용자 코드, Java 21
public class Client {
    public static void main(String[] args) {
        try {
            Lib.foo(1);
            Lib.foo(-1);
        } catch (A e) {
            System.out.println("caught A");
        }
    }
}
