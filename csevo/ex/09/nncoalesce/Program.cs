// 슬라이드 p9-v8-tcoalesce — 제약 없는 T 에 ??, C# 8.0
using System;

class App
{
    // T may be a class, a struct or a Nullable<T>
    static T Or<T>(T value, T fallback) => value ?? fallback;

    static void Main()
    {
        Console.WriteLine(Or<string>(null, "fallback"));
        Console.WriteLine(Or<int?>(null, 3));
        Console.WriteLine(Or<int>(0, 5));      // an int is never null
    }
}
