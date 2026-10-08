// 슬라이드 p1-design-overload — 같은 모양을 자바에서, Java 21
class Base {
    public void f(int x) { System.out.println("Base.f(int)"); }
}

class Derived extends Base {
    public void f(double x) { System.out.println("Derived.f(double)"); }
}

public class Main {
    public static void main(String[] args) {
        Derived d = new Derived();
        d.f(1);                    // int argument
        ((Base) d).f(1);
    }
}
