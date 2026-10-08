// 슬라이드 p7-v6-nullcond-generic — 형식 매개변수 T, C# 6.0
using System;

class Box<T>
{
    public T Value;
    public Box(T v) { Value = v; }
}

class App
{
    static string Text<T>(Box<T> b)
    {
        return b?.Value?.ToString() ?? "null";    // result is string
    }

    static int? Hash<T>(Box<T> b) where T : struct
    {
        return b?.Value.GetHashCode();            // known value type
    }

    static T Ref<T>(Box<T> b) where T : class
    {
        return b?.Value;                          // stays T
    }

    static void Main()
    {
        Console.WriteLine(Text(new Box<int>(5)));
        Console.WriteLine(Text<string>(null));
        Console.WriteLine(Text(new Box<string>(null)));
        Console.WriteLine(Hash(new Box<int>(7)));
        Console.WriteLine(Ref<string>(null) == null);
    }
#if BAD
    static T Get<T>(Box<T> b) { return b?.Value; }   // T unknown
#endif
}
