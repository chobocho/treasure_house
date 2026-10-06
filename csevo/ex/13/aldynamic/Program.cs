// 슬라이드 p13-v12-al-dynamic — dynamic 별칭은 C# 12 전에도, C# 12.0
using System;
using Dyn = dynamic;

class App
{
    static void Main()
    {
        Dyn d = "hello";
        Console.WriteLine(d.Length);
        d = 41;
        Console.WriteLine(d + 1);
    }
}
