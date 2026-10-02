// 슬라이드 p9-v8-dim-vsext — 확장 메서드와 기본 구현, C# 8.0
using System;

interface IOld { string Name { get; } }
static class OldExt                        // the C# 3 way
{
    public static string Hello(this IOld o) => "ext: hi " + o.Name;
}

interface INew
{
    string Name { get; }
    string Hello() => "default: hi " + Name;   // the C# 8 way
}

// both classes try to supply a better Hello
class A : IOld
{
    public string Name => "A";
    public string Hello() => "A's own Hello";
}
class B : INew
{
    public string Name => "B";
    public string Hello() => "B's own Hello";
}

class App
{
    static void Main()
    {
        IOld a = new A();
        INew b = new B();
        Console.WriteLine(a.Hello());      // bound at compile time
        Console.WriteLine(b.Hello());      // dispatched at run time
    }
}
