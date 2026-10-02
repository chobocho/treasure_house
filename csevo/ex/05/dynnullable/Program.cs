// 슬라이드 p5-v4-dyn-nullable — 뒤 버전: dynamic? 과 nullable, C# 8.0
using System;

class Program
{
    static void Main()
    {
        dynamic? maybe = null;
        dynamic sure = "text";
        Console.WriteLine(sure.Length);
        Console.WriteLine(maybe == null);
#if BAD
        dynamic bad = null;              // CS8600
        Console.WriteLine(bad == null);
        Console.WriteLine(maybe.Length); // CS8602
#endif
    }
}
