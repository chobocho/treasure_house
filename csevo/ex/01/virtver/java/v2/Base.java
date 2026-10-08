// 슬라이드 p1-design-virt-java — 기반 2판: foo 를 더해 부른다, Java 21
public class Base {
    public void run() {
        System.out.println("Base.run");
        foo();
    }

    public void foo() {
        System.out.println("Base.foo: new hook in version 2");
    }
}
