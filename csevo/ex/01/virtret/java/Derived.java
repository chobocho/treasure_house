// 슬라이드 p1-design-virt-ret — 같은 이름, 다른 반환 형식, Java 21
public class Derived extends Base {
    public int foo() {
        System.out.println("Derived.foo: counts files");
        return 3;
    }
}
