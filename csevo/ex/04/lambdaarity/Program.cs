// 슬라이드 p4-v3-lambda-vsanon — 람다는 매개변수 수가 맞아야, C# 3.0
using System;

class App
{
    static void Main()
    {
        Action<int> c = () => Console.WriteLine("no x");
        Func<int, int> d = x => { x + 1; };
        c(1);
    }
}
