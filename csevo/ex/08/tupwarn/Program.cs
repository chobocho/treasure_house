// 슬라이드 p8-v7-tuple-warn — 리터럴의 이름이 버려질 때, C# 7.0
using System;

class App
{
    static (int width, int height) Size()
    {
        return (height: 1080, width: 1920);  // names don't reorder
    }

    static void Main()
    {
        var s = Size();
        Console.WriteLine("width=" + s.width);
        (int a, int b) t = (b: 1, a: 2);
        Console.WriteLine(t.a);
    }
}
