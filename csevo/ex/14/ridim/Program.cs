// 슬라이드 p14-v13-ri-dim — 기본 구현이 있어도 다 구현, C# 13.0
using System;

interface IGreet
{
    string Name();
    string Hello() => "hello " + Name();   // default implementation
#if SEALED
    sealed string Shout() => Hello().ToUpperInvariant();
#endif
}

ref struct R : IGreet
{
    public string Name() => "ref";
#if !MISSING
    public string Hello() => "hi " + Name();  // required here
#endif
}

class C : IGreet
{
    public string Name() => "class";          // may rely on the default
}

class App
{
    static string Greet<T>(T t) where T : IGreet, allows ref struct
#if SEALED
        => t.Shout();
#else
        => t.Hello();
#endif

    static void Main()
    {
        Console.WriteLine(Greet(new R()));
        Console.WriteLine(Greet(new C()));
    }
}
