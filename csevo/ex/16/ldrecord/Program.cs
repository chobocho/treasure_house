// 슬라이드 p16-ld-record — record 는 사다리에 못 오른다, C# 9.0
using System;

record Point(int X, int Y);

class Program
{
    static void Main()
    {
        Point p = new Point(1, 2);
        Console.WriteLine(p);
    }
}
