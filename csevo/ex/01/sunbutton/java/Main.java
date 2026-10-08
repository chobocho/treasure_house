// 슬라이드 p1-java-sun — Sun 이 권한 길: 안쪽 클래스 어댑터, Java 21
import java.util.ArrayList;
import java.util.List;

interface ActionListener {
    void actionPerformed(String command);
}

class Button {
    private final List<ActionListener> listeners = new ArrayList<>();
    private final String label;
    Button(String label) { this.label = label; }
    void addActionListener(ActionListener l) { listeners.add(l); }
    void click() {
        for (ActionListener l : listeners) l.actionPerformed(label);
    }
}

public class Main {
    Button ok = new Button("OK");

    Main() {
        // anonymous inner class: the adapter Sun recommended
        ok.addActionListener(new ActionListener() {
            public void actionPerformed(String command) {
                System.out.println("Hello, " + command + "!");
            }
        });
    }

    public static void main(String[] args) {
        new Main().ok.click();
    }
}
