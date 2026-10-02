// 슬라이드 p8-v7_3-enumdel — Enum·Delegate 제약, C# 7.3
using System;

enum Color { Red, Green, Blue }

class App
{
    static string Names<T>() where T : struct, Enum
    {
        return string.Join(",", Enum.GetNames(typeof(T)));
    }

    static T Parse<T>(string s) where T : struct, Enum
    {
        return (T)Enum.Parse(typeof(T), s);   // no 'object' detour
    }

    static D Both<D>(D a, D b) where D : Delegate
    {
        return (D)Delegate.Combine(a, b);
    }

    static void Main()
    {
        Console.WriteLine(Names<Color>());
        Console.WriteLine((int)(object)Parse<Color>("Blue"));
        Action hi = Both<Action>(() => Console.Write("a"),
                                 () => Console.WriteLine("b"));
        hi();
#if BAD
        Console.WriteLine(Names<int>());       // int is not an enum
#endif
    }
}
