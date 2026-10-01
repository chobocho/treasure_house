// 슬라이드 p3-v2-overload — 제네릭과 비제네릭 오버로드, C# 2.0
using System;

class App
{
    static void Show(object x) { Console.WriteLine("object  " + x); }
    static void Show(string x) { Console.WriteLine("string  " + x); }

    static void Show<T>(T x)
    {
        Console.WriteLine("T=" + typeof(T).Name + " " + x);
    }

    static void Main()
    {
        Show(1);              // Show<int>: exact, no boxing
        Show("s");            // tie with Show<string>: non-generic
        Show((object)2);      // tie with Show<object>: non-generic
        Show<string>("t");    // explicit: only the generic fits
    }
}
