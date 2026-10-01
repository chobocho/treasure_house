// 슬라이드 p3-v2-as-trap — 제약 없는 T 에 as 를 쓰면, C# 2.0
using System;

class App
{
    static T Get<T>(object o)
    {
        return o as T;
    }

    static void Main()
    {
        Console.WriteLine(Get<string>("s"));
    }
}
