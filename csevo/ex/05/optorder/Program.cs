// 슬라이드 p5-v4-named-order — 인수는 적힌 차례로 평가된다, C# 4.0
using System;

class Program
{
    static void F(int x, int y = -1, int z = -2)
    {
        Console.WriteLine("x = " + x + ", y = " + y + ", z = " + z);
    }

    static int Say(string name, int v)
    {
        Console.WriteLine("  evaluating " + name);
        return v;
    }

    static void Main()
    {
        int i = 0;
        F(i++, i++, i++);
        F(z: i++, x: i++);
        F(z: Say("z", 30), x: Say("x", 10));
    }
}
