// 슬라이드 p3-v2-default-t — T 에 null 을 돌려주면, C# 2.0
using System;

class App
{
    static T Nothing<T>()
    {
        return null;
    }

    static void Main()
    {
        Console.WriteLine(Nothing<string>());
    }
}
