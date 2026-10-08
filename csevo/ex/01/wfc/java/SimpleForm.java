// 슬라이드 p1-java-wfc — J++ 의 대리자 문법을 표준 자바에, Java 21
delegate void EventHandler(Object sender, Object e);

class SimpleForm {
    void buttonOK_click(Object sender, Object e) {
        System.out.println("Clicked OK");
    }

    void initForm() {
        EventHandler h = new EventHandler(this.buttonOK_click);
    }
}
