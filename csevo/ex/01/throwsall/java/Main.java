// 슬라이드 p1-design-exc-swallow — throws Exception·빈 catch, Java 21
public class Main {
    static int parse(String s) throws Exception {
        return Integer.parseInt(s);
    }

    public static void main(String[] args) {
        int total = 0;
        String[] input = { "1", "two", "3" };
        for (String s : input) {
            try {
                total += parse(s);
            } catch (Exception e) { }   // "fix it later"
        }
        System.out.println("total = " + total);
    }
}
