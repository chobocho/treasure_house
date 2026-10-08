// 슬라이드 p1-java-count — 메뉴 셋, 어댑터 셋, Java 21
interface ActionListener {
    void actionPerformed(String command);
}

class MenuItem {
    final String text;
    ActionListener listener;
    MenuItem(String text) { this.text = text; }
    void click() { listener.actionPerformed(text); }
}

public class Editor {
    MenuItem open = new MenuItem("Open"), save = new MenuItem("Save"),
             exit = new MenuItem("Exit");

    void notYet(String what) {
        System.out.println(what + ": not implemented");
    }

    Editor() {
        open.listener = new ActionListener() {
            public void actionPerformed(String c) { notYet(c); } };
        save.listener = new ActionListener() {
            public void actionPerformed(String c) { notYet(c); } };
        exit.listener = new ActionListener() {
            public void actionPerformed(String c) { notYet(c); } };
    }

    public static void main(String[] args) {
        Editor e = new Editor();
        e.open.click(); e.save.click(); e.exit.click();
    }
}
