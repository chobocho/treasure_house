// 슬라이드 p1-design-del-java — 한 클래스, 두 출처, 어댑터 둘, Java 21
interface ActionListener {
    void actionPerformed(Object source);
}

class Button {
    final String name;
    ActionListener listener;
    Button(String name) { this.name = name; }
    void click() { listener.actionPerformed(this); }
}

public class Dialog {
    Button ok = new Button("OK"), cancel = new Button("Cancel");
    void onOk() { System.out.println("Dialog: accept"); }
    void onCancel() { System.out.println("Dialog: close"); }

    Dialog() {
        ok.listener = new ActionListener() {
            public void actionPerformed(Object s) { onOk(); } };
        cancel.listener = new ActionListener() {
            public void actionPerformed(Object s) { onCancel(); } };
    }

    public static void main(String[] args) {
        Dialog d = new Dialog();
        d.ok.click();
        d.cancel.click();
    }
}
