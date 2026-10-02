// 슬라이드 p8-v7-tuple-conv — 이름이 달라도 자리로 바뀐다, C# 7.0
using System;

class App
{
    static (int width, int height) Size() => (1920, 1080);

    static void Main()
    {
        (int w, int h) a = Size();          // renamed: fine
        Console.WriteLine(a.w + "x" + a.h);

        (int height, int width) b = Size(); // names swapped!
        Console.WriteLine("height=" + b.height);

        (long, double) c = Size();          // element-wise widening
        Console.WriteLine(c);

        var d = ((int, int))(3L, 4.9);      // explicit, element-wise
        Console.WriteLine(d);
    }
}
