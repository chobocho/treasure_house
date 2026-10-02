// 슬라이드 p10-v9-records — 레코드 선언, C# 9.0
using System;

record Point(int X, int Y);

class App
{
    static void Main()
    {
        Point p = new Point(1, 2);
        Console.WriteLine(p);
        Console.WriteLine(p == new Point(1, 2));
    }
}
