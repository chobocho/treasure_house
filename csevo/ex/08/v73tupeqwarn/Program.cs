// 슬라이드 p8-v7_3-tupleeq-names — 이름은 비교하지 않는다, C# 7.3
using System;

class App
{
    static void Main()
    {
        (int a, int b) t = (1, 2);
        Console.WriteLine(t == (b: 1, a: 2));   // names are not matched
        Console.WriteLine(t == (1, 2));
    }
}
