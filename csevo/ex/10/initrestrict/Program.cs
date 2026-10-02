// 슬라이드 p10-v9-init-restrict — init 의 제약, C# 9.0
class C
{
    public static int S { get; init; }       // static
    public int B { get; set; init; }         // both set and init
    public int F { init; }                   // init only, no get
}

class App
{
    static void Main() { }
}
