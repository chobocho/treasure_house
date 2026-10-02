// 슬라이드 p8-v7-tuple-swap — 바꿔 넣기와 평가 순서, C# 7.0
using System;

class Box
{
    int a = 1, b = 2;
    public int A
    {
        get { Console.WriteLine("  get A"); return a; }
        set { Console.WriteLine("  set A=" + value); a = value; }
    }
    public int B
    {
        get { Console.WriteLine("  get B"); return b; }
        set { Console.WriteLine("  set B=" + value); b = value; }
    }
}

class App
{
    static void Main()
    {
        int x = 1, y = 2;
        (x, y) = (y, x);                // no temp variable written
        Console.WriteLine(x + " " + y);

        var box = new Box();
        Console.WriteLine("swap:");
        (box.A, box.B) = (box.B, box.A);
        Console.WriteLine(box.A + " " + box.B);
    }
}
