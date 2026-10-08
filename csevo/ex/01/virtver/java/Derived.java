// 슬라이드 p1-design-virt-java — 1판 시절에 쓴 파생 클래스, Java 21
public class Derived extends Base {
    public void foo() {   // a private helper, as far as the author knew
        System.out.println("Derived.foo: deletes temp files");
    }
}
