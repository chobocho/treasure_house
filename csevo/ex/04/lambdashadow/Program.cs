// 슬라이드 p4-v3-lambda-shadow — 바깥 이름을 가리는 매개변수, C# 8
using System;

class App
{
    static void Main()
    {
        int x = 10;
        Func<int, int> twice = x => x * 2;    // this x is the parameter
        Console.WriteLine(twice(3) + " " + x);
    }
}
