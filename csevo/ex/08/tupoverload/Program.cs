// 슬라이드 p8-v7-tuple-overload — 이름만 다른 시그니처, C# 7.0
class Base
{
    public virtual (int x, int y) Get() => (1, 2);
}

class Derived : Base
{
    public override (int a, int b) Get() => (3, 4);   // renamed
}

class App
{
    static void M((int x, int y) p) { }
    static void M((int a, int b) p) { }               // same type

    static void Main() { }
}
