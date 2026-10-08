// 슬라이드 p1-design-box-java — 원시 형식과 감싸개 클래스, Java 21
import java.util.ArrayList;

public class Wrap {
    public static void main(String[] args) {
        Integer boxed = new Integer(42);   // hand-made wrapper
        Object o = boxed;
        System.out.println(o.getClass().getName());
        System.out.println(Integer.toHexString(42).toUpperCase());

        ArrayList<Object> list = new ArrayList<Object>();
        list.add(Integer.valueOf(1));
        list.add("two");
        list.add(Double.valueOf(3.5));
        for (Object x : list)
            System.out.println(x.getClass().getSimpleName() + " " + x);

        int back = ((Integer) list.get(0)).intValue();
        System.out.println(back + 1);
    }
}
