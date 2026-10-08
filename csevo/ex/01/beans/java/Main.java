// 슬라이드 p1-design-comp-java — 속성은 이름 짓기 규칙, Java 21
import java.beans.Introspector;
import java.beans.PropertyDescriptor;
import java.lang.reflect.Method;

public class Main {
    public static class Person {
        private String name;
        private boolean active;
        public String getName() { return name; }
        public void setName(String n) { name = n; }
        public boolean isActive() { return active; }
    }

    static String nameOf(Method m) {
        return m == null ? "-" : m.getName();
    }

    public static void main(String[] args) throws Exception {
        PropertyDescriptor[] ps = Introspector
            .getBeanInfo(Person.class, Object.class)
            .getPropertyDescriptors();
        for (PropertyDescriptor p : ps)
            System.out.println("property " + p.getName()
                + " read=" + nameOf(p.getReadMethod())
                + " write=" + nameOf(p.getWriteMethod()));
    }
}
