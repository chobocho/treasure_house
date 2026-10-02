// 슬라이드 p8-v7-ref-structfld — 구조체의 필드를 ref 로, C# 7.0
struct S
{
    public int X;

    public ref int Mine()
    {
        return ref X;            // 'this' of a struct: not allowed
    }
}

class C
{
    public int X;
    public ref int Mine() { return ref X; }   // a class: fine
}

class App
{
    static ref int FromRef(ref S s) { return ref s.X; }  // fine
    static ref int FromVal(S s) { return ref s.X; }      // a copy

    static void Main()
    {
    }
}
