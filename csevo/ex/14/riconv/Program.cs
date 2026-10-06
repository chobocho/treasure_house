// 슬라이드 p14-v13-ri-conv — 인터페이스 형식으로는 못 바꾼다, C# 13.0
using System;

interface IName { string Name(); }

ref struct Tag : IName
{
    string IName.Name() => "tag";     // explicit implementation
}

class App
{
    static string Call<T>(T t) where T : IName, allows ref struct
        => t.Name();                  // reaches the explicit one

    static void Main()
    {
        var t = new Tag();
        Console.WriteLine(Call(t));
#if CONV
        IName n = t;                  // would box
#elif CAST
        Console.WriteLine(((IName)t).Name());
#elif PAT
        Console.WriteLine(t is IName);
#elif DIRECT
        Console.WriteLine(t.Name());  // explicit: not on Tag
#endif
    }
}
