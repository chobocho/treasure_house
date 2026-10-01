// 슬라이드 p3-v2-variance — 변성을 직접 선언하기, C# 4.0
using System;

interface IBox<out T>
{
    T Get();
}

class StrBox : IBox<string>
{
    public string Get() { return "s"; }
}

class App
{
    static void Main()
    {
        IBox<object> b = new StrBox();
        Console.WriteLine(b.Get());
    }
}
