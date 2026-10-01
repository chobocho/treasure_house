// 슬라이드 p3-v2-as-trap — class 제약과 is 로 고치기, C# 2.0
using System;

class App
{
    static T GetRef<T>(object o) where T : class
    {
        return o as T;                    // null when it is not a T
    }

    static T GetAny<T>(object o)
    {
        return o is T ? (T)o : default(T);
    }

    static void Main()
    {
        Console.WriteLine(GetRef<string>("s"));
        Console.WriteLine(GetRef<string>(42) == null);
        Console.WriteLine(GetAny<int>(42) + GetAny<int>("x"));
    }
}
