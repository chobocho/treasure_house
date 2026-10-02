// 슬라이드 p10-v9-pm-rules — 새 규칙의 partial 메서드, C# 9.0
partial class C
{
    partial void M1();                  // old rules: may stay empty
    private partial void M2();
    private partial void M3();          // new rules: needs a body
    public partial int M4();
    internal partial void M5(out int x);
}

partial class C
{
    private partial void M2() { }
    internal partial int M4() => 4;     // access differs
    internal partial void M5(out int y) { y = 5; }   // name only
}

class App
{
    static void Main() { }
}
