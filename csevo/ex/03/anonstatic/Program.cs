// 슬라이드 p3-v2-anon-static — static 익명 메서드, C# 9
using System;

delegate int Op(int x);

class App
{
    static void Main()
    {
        Op twice = static delegate(int x) { return x * 2; };
        Console.WriteLine(twice(21));
    }
}
