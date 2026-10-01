// 슬라이드 p2-v1-propname — 속성이 예약하는 이름, C# 1.0
class Person
{
    public string Name
    {
        get { return "kim"; }
    }

    public string get_Name() { return "clash"; }
    public void set_Name(string v) { }
}

class App
{
    static void Main() { }
}
