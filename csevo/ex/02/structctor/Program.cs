// 슬라이드 p2-v1-struct — 구조체 생성자는 모든 필드를, C# 1.0
using System;

struct Size
{
    public int W;
    public int H;

    public Size(int w)
    {
        W = w;               // H is never assigned
    }

    public void Grow() { H += 1; }
}

class App
{
    static void Main()
    {
        Size a = new Size(3);
        Size b = new Size();     // always exists: all zero
        Console.WriteLine(a.W + "x" + a.H + ", " + b.W + "x" + b.H);
    }
}
