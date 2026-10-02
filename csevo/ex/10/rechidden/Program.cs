// 슬라이드 p10-v9-rec-hidden — 가려진 기반 멤버를 위치 멤버로, C# 9.0
record Base
{
    public int I { get; init; }
}

record Derived(int I) : Base   // positional member found: Base.I
{
    public int I() { return 0; }   // ... but hidden by this method
}

class App
{
    static void Main() { }
}
