// 슬라이드 p3-v2-nullable-generic — 제네릭 안의 T?, C# 2.0
using System;

class App
{
    static T? Some<T>(T x) where T : struct
    {
        return x;                         // T? is Nullable<T>
    }

    static void Main()
    {
        Console.WriteLine(Some(5).HasValue);
        Console.WriteLine(Some(2.5).GetValueOrDefault());
    }
}
