// 슬라이드 p9-v8-co-nullable — int? 에 쓴 ??= 의 형식, C# 8.0
using System;

class App
{
    static string TypeOf<T>(T _) => typeof(T).Name;

    static void Main()
    {
        int? i = null;
        string s = null;

        Console.WriteLine(TypeOf(i ??= 5));     // int, not int?
        Console.WriteLine(TypeOf(i ?? 6));      // int too
        Console.WriteLine(TypeOf(s ??= "x"));   // string

        int j = (i ??= 7);                      // no cast needed
        Console.WriteLine(j);                   // 5: i was not null
    }
}
