// 슬라이드 p1-design-del-java — 지금의 자바: 메서드 참조, Java 21
public class Modern {
    Button ok = new Button("OK"), cancel = new Button("Cancel");
    void onOk(Object s) { System.out.println("Modern: accept"); }
    void onCancel(Object s) { System.out.println("Modern: close"); }

    public static void main(String[] args) {
        Modern m = new Modern();
        m.ok.listener = m::onOk;          // still an ActionListener
        m.cancel.listener = m::onCancel;
        m.ok.click();
        m.cancel.click();
        System.out.println(m.ok.listener instanceof ActionListener);
    }
}
