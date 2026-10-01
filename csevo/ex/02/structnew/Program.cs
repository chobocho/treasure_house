// 슬라이드 p2-v1-structnew — new 없는 구조체 변수와 기본값, C# 1.0
using System;

struct Point
{
    public int X, Y;
    public override string ToString() { return X + "," + Y; }
}

class App
{
    static void Main()
    {
        Point p;                          // no new: fields unassigned
        p.X = 1;
        p.Y = 2;                          // now p is fully assigned
        Console.WriteLine(p.ToString());

        Point[] pts = new Point[1];       // array elements start zeroed
        string[] names = new string[1];   // ...or null
        bool[] flags = new bool[1];
        Console.WriteLine(pts[0] + " " + (names[0] == null) + " "
            + flags[0]);
        Console.WriteLine(new int() + " " + new bool() + " "
            + (int)new char());
    }
}
