// 슬라이드 p4-v3-anon-cast — 메서드 밖으로는 object 로, C# 3.0
using System;

class App
{
    static object Make()
    {
        return new { Name = "Ann", Age = 31 };
    }

    // "cast by example": T is inferred from the example's type
    static T CastLike<T>(object o, T example)
    {
        return (T)o;
    }

    static void Main()
    {
        object o = Make();
        Console.WriteLine(o);

        var p = CastLike(o, new { Name = "", Age = 0 });
        Console.WriteLine(p.Name + " is " + p.Age);
    }
}
