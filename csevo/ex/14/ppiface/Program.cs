// 슬라이드 p14-v13-pp-iface — 인터페이스의 partial 멤버, C# 13.0
using System;

partial interface I
{
    public partial int P { get; }
    public partial int P => 1;       // property: implicitly virtual
    public partial int M();
    public partial int M() => 1;     // method: implicitly non-virtual
}

class C : I
{
    public int P => 2;
    public int M() => 2;
}

class App
{
    static void Main()
    {
        I i = new C();
        Console.WriteLine("P " + i.P + ", M " + i.M());
        var get = typeof(I).GetProperty("P").GetMethod;
        var m = typeof(I).GetMethod("M");
        Console.WriteLine("virtual: P " + get.IsVirtual
            + ", M " + m.IsVirtual);
    }
}
