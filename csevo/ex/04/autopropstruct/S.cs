// 슬라이드 p4-v3-autoprop-struct — 구조체 생성자와 자동 속성, C# 11
using System;

struct Size
{
    public int W { get; set; }
    public int H { get; set; }

    public Size(int w)       // H is never assigned
    {
        W = w;
    }
}

class App
{
    static void Main()
    {
        Size s = new Size(3);
        Console.WriteLine(s.W + " x " + s.H);
    }
}
