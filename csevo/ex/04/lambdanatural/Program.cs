// 슬라이드 p4-v3-lambda-natural — 람다의 자연 형식, C# 10
using System;

class App
{
    static void Main()
    {
        var inc = (int x) => x + 1;          // Func<int, int>
        var hello = () => Console.WriteLine("hello");
        Console.WriteLine(inc.GetType().Name + " " + inc(1));
        Console.WriteLine(hello.GetType().Name);
        hello();
    }
}
