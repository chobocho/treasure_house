// 슬라이드 p10-v9-pat-dag — 결합 패턴도 검사를 나눠 쓴다, C# 9.0
using System;

class Box
{
    public static int Reads;
    readonly int w, h;
    public Box(int w, int h) { this.w = w; this.h = h; }
    public int W { get { Reads++; return w; } }
    public int H { get { Reads++; return h; } }
}

class App
{
    static string Size(Box b) => b switch
    {
        { W: < 0 } or { H: < 0 } => "bad",
        { W: 0 } or { H: 0 } => "empty",
        { W: < 10, H: < 10 } => "small",
        { W: >= 10 and < 100 } or { H: >= 10 and < 100 } => "medium",
        _ => "large",
    };

    static void Main()
    {
        int[][] all = { new[] { -1, 5 }, new[] { 3, 0 }, new[] { 4, 4 },
                        new[] { 50, 500 }, new[] { 500, 500 } };
        foreach (int[] s in all)
        {
            Box.Reads = 0;
            string r = Size(new Box(s[0], s[1]));
            Console.WriteLine(s[0] + "x" + s[1] + " " + r
                              + " (reads " + Box.Reads + ")");
        }
    }
}
